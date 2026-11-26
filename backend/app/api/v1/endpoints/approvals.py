import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.investigation import Investigation
from app.database.models.approval import Approval, Report
from app.database.repositories.investigation_repository import InvestigationRepository
from app.database.repositories.approval_repository import ApprovalRepository
from app.database.repositories.audit_repository import AuditRepository
from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.schemas.common import SuccessResponse
from app.core.dependencies import get_current_user, require_auditor
from app.investigation.stream_manager import stream_manager

router = APIRouter()

@router.post("/{investigation_id}", response_model=SuccessResponse[ApprovalResponse])
async def submit_approval(
    investigation_id: str,
    approval_in: ApprovalRequest,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    # Enforce Auditor role: Admin is responsible for administration, not auto-approving investigations
    if current_user.role.upper() not in ["AUDITOR", "ACCOUNTANT"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Auditors are authorized to review and approve GST investigation responses."
        )
    inv_repo = InvestigationRepository(db)
    inv = await inv_repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    action = approval_in.action.upper()
    if action not in ["APPROVE", "EDIT", "REJECT", "REQUEST_MORE_EVIDENCE"]:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    latest_report = next((r for r in (inv.reports or []) if r.is_latest), None)
    wf_state = dict(inv.workflow_state or {})
    draft_content = (latest_report.content if latest_report else None) or wf_state.get("response_draft")

    if action == "APPROVE":
        if inv.status == "APPROVED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Investigation has already been approved and finalized."
            )
        if not draft_content and not approval_in.edited_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot approve investigation: No response draft has been generated or saved."
            )

    # Create Approval record
    app_id = uuid.uuid4()
    approval = Approval(
        id=app_id,
        investigation_id=inv.id,
        reviewer_id=current_user.id,
        action=action,
        notes=approval_in.notes,
        edited_content=approval_in.edited_content,
        is_final=(action == "APPROVE")
    )
    db.add(approval)

    # Update Investigation status & Report persistence
    if action == "APPROVE":
        inv.status = "APPROVED"
        merged_content = dict(draft_content or {})
        if approval_in.edited_content:
            merged_content.update(approval_in.edited_content)

        if latest_report:
            latest_report.report_type = "FINAL"
            latest_report.content = merged_content
            if merged_content.get("title"):
                latest_report.title = merged_content["title"]
        else:
            db.add(Report(
                id=uuid.uuid4(),
                investigation_id=inv.id,
                report_type="FINAL",
                title=merged_content.get("title") or f"Final Report — {inv.title}",
                content=merged_content,
                is_latest=True,
                generated_by=current_user.full_name or current_user.email
            ))
        await stream_manager.broadcast(str(inv.id), "investigation_completed", {
            "status": "APPROVED",
            "action": "APPROVE",
            "notes": approval_in.notes
        })
    elif action == "EDIT":
        if approval_in.edited_content:
            merged_content = dict(draft_content or {})
            merged_content.update(approval_in.edited_content)
            if latest_report:
                latest_report.content = merged_content
                if merged_content.get("title"):
                    latest_report.title = merged_content["title"]
            else:
                db.add(Report(
                    id=uuid.uuid4(),
                    investigation_id=inv.id,
                    report_type="RESPONSE_DRAFT",
                    title=merged_content.get("title") or f"Response Draft — {inv.title}",
                    content=merged_content,
                    is_latest=True,
                    generated_by=current_user.full_name or current_user.email
                ))
            wf_state["response_draft"] = merged_content
            inv.workflow_state = wf_state
        await stream_manager.broadcast(str(inv.id), "draft_edited", {
            "status": inv.status,
            "notes": approval_in.notes
        })
    elif action == "REJECT":
        inv.status = "REJECTED"
        await stream_manager.broadcast(str(inv.id), "investigation_failed", {
            "status": "REJECTED",
            "action": "REJECT",
            "notes": approval_in.notes
        })
    elif action == "REQUEST_MORE_EVIDENCE":
        inv.status = "NEEDS_MORE_EVIDENCE"
        await stream_manager.broadcast(str(inv.id), "investigation_needs_evidence", {
            "status": "NEEDS_MORE_EVIDENCE",
            "notes": approval_in.notes
        })

    audit_repo = AuditRepository(db)
    await audit_repo.log_action(
        action=f"AUDITOR_{action}",
        resource_type="investigation",
        resource_id=str(inv.id),
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        details={"notes": approval_in.notes, "new_status": inv.status}
    )

    await db.commit()

    return SuccessResponse(
        data=ApprovalResponse(
            id=str(approval.id),
            investigation_id=str(approval.investigation_id),
            reviewer_id=str(approval.reviewer_id),
            action=approval.action,
            notes=approval.notes,
            is_final=approval.is_final,
            created_at=approval.created_at
        ),
        message=f"Action '{action}' recorded successfully"
    )

@router.get("/{investigation_id}", response_model=SuccessResponse[List[ApprovalResponse]])
async def get_approval_history(
    investigation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ApprovalRepository(db)
    approvals = await repo.get_by_investigation(investigation_id)
    return SuccessResponse(
        data=[
            ApprovalResponse(
                id=str(a.id),
                investigation_id=str(a.investigation_id),
                reviewer_id=str(a.reviewer_id),
                action=a.action,
                notes=a.notes,
                is_final=a.is_final,
                created_at=a.created_at
            )
            for a in approvals
        ]
    )
