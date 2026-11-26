import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.database.repositories.investigation_repository import InvestigationRepository
from app.database.repositories.approval_repository import ApprovalRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.audit_repository import AuditRepository
from app.schemas.approval import ReportResponse
from app.schemas.common import SuccessResponse
from app.core.dependencies import get_current_user
from app.config.security import decode_access_token
from app.services.report_service import pdf_service

router = APIRouter()

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads", "reports"))


@router.get("/{investigation_id}", response_model=SuccessResponse[ReportResponse])
async def get_report_by_investigation(
    investigation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    inv_repo = InvestigationRepository(db)
    inv = await inv_repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    repo = ApprovalRepository(db)
    report = await repo.get_report_by_investigation(investigation_id)
    if not report:
        # Check if workflow_state has a response_draft
        wf_draft = (inv.workflow_state or {}).get("response_draft")
        if not wf_draft:
            raise HTTPException(status_code=404, detail="Report not found for this investigation")
        return SuccessResponse(
            data=ReportResponse(
                id=str(inv.id),
                investigation_id=str(inv.id),
                report_type="RESPONSE_DRAFT",
                title=wf_draft.get("title") or f"Response Draft — {inv.title}",
                content=wf_draft,
                pdf_path=None,
                is_latest=True,
                generated_by="Response Drafter Agent",
                created_at=inv.updated_at or inv.created_at
            )
        )

    return SuccessResponse(
        data=ReportResponse(
            id=str(report.id),
            investigation_id=str(report.investigation_id),
            report_type=report.report_type,
            title=report.title,
            content=report.content,
            pdf_path=report.pdf_path,
            is_latest=report.is_latest,
            generated_by=report.generated_by,
            created_at=report.created_at
        )
    )


@router.get("/{id}/pdf")
@router.get("/{id}/download")
async def download_report_pdf(
    id: str,
    token: Optional[str] = Query(None),
    auth_header: Optional[str] = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db)
):
    """
    Downloadable audit-ready PDF investigation report package.
    Enforces authentication, organization isolation, and APPROVED status.
    Persists generated PDF to disk on first download for deterministic re-downloads.
    """
    jwt_token = token
    if not jwt_token and auth_header and auth_header.startswith("Bearer "):
        jwt_token = auth_header.split(" ")[1]

    if not jwt_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required to download report PDF.")

    payload = decode_access_token(jwt_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    inv_repo = InvestigationRepository(db)
    approval_repo = ApprovalRepository(db)

    inv = await inv_repo.get_with_details(id)
    report = None

    if inv:
        report = next((r for r in (inv.reports or []) if r.is_latest), None)
    else:
        report = await approval_repo.get_report_by_id(id)
        if report:
            inv = await inv_repo.get_with_details(str(report.investigation_id))

    if not inv:
        raise HTTPException(status_code=404, detail="Investigation or report not found")

    if str(inv.organization_id) != str(user.organization_id):
        raise HTTPException(status_code=403, detail="Forbidden: Organization mismatch")

    if inv.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Final PDF report is only available after Auditor approval (current status: {inv.status})."
        )

    filename = f"TaxPilot_Final_Report_{str(inv.id)[:8]}_{inv.tax_period or 'GST'}.pdf"

    # If PDF already saved on disk, return the exact persisted file
    if report and report.pdf_path and os.path.exists(report.pdf_path):
        with open(report.pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    content = report.content if report and report.content else {}
    if not content and inv.workflow_state and inv.workflow_state.get("response_draft"):
        content = inv.workflow_state.get("response_draft")

    wf_state = inv.workflow_state or {}

    verified_findings = []
    if wf_state.get("verification_details", {}).get("verified_findings"):
        verified_findings = wf_state["verification_details"]["verified_findings"]
    elif wf_state.get("evaluated_hypotheses"):
        for h in wf_state["evaluated_hypotheses"]:
            if h.get("status") == "SUPPORTED":
                verified_findings.append({
                    "finding_type": h.get("hypothesis_type", "FINDING"),
                    "title": h.get("title", "Verified Finding"),
                    "evidence_ids": h.get("supporting_evidence_ids", [])
                })

    notice_data = wf_state.get("notice_data") or {}
    if not notice_data and inv.notice:
        notice_data = {
            "notice_number": inv.notice.notice_number,
            "notice_type": inv.notice.notice_type,
            "itc_claimed": float(inv.notice.itc_claimed or 0.0),
            "itc_available": float(inv.notice.itc_available or 0.0),
            "itc_mismatch": float(inv.notice.itc_mismatch or inv.mismatch_amount or 0.0),
            "response_deadline": str(inv.notice.response_deadline or inv.response_deadline or "N/A")
        }

    # Get latest approval record
    approvals = await approval_repo.get_by_investigation(str(inv.id))
    final_approval = next((a for a in approvals if a.action == "APPROVE"), None)
    approver_name = (
        (final_approval.reviewer.full_name or final_approval.reviewer.email)
        if final_approval and final_approval.reviewer
        else (user.full_name or user.email)
    )
    approval_notes = final_approval.notes if final_approval else ""
    approved_at = final_approval.created_at.strftime("%Y-%m-%d %H:%M UTC") if final_approval and final_approval.created_at else None

    pdf_bytes = pdf_service.generate_investigation_pdf(
        investigation_title=inv.title,
        client_name=inv.client.business_name if inv.client else "Taxpayer",
        client_gstin=inv.client.primary_gstin if inv.client else (notice_data.get("gstin") or "N/A"),
        tax_period=inv.tax_period or notice_data.get("tax_period") or "N/A",
        mismatch_amount=float(inv.mismatch_amount or notice_data.get("itc_mismatch") or 0.0),
        notice_data=notice_data,
        verified_findings=verified_findings,
        response_draft=content,
        suspect_invoices=wf_state.get("suspect_invoices", []),
        verification_verdict=wf_state.get("verification_verdict", "VERIFIED"),
        approver_name=approver_name,
        approval_notes=approval_notes,
        approved_at=approved_at,
    )

    # Persist PDF to disk and store path on Report record
    os.makedirs(REPORTS_DIR, exist_ok=True)
    pdf_file_path = os.path.join(REPORTS_DIR, f"{inv.id}.pdf")
    with open(pdf_file_path, "wb") as f:
        f.write(pdf_bytes)

    if report:
        report.pdf_path = pdf_file_path
        await db.commit()

    # Phase 7: Audit trail — log PDF download
    try:
        audit_repo = AuditRepository(db)
        await audit_repo.log_action(
            action="PDF_DOWNLOADED",
            resource_type="report",
            resource_id=str(inv.id),
            user_id=str(user.id),
            organization_id=str(user.organization_id),
            details={"filename": filename, "investigation_title": inv.title}
        )
        await db.commit()
    except Exception:
        pass  # Audit failure must never block the download

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
