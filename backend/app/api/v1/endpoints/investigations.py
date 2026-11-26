import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Header, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.database.session import get_db, AsyncSessionLocal
from app.database.models.user import User
from app.database.models.investigation import Investigation
from app.database.models.notice import Notice, UploadedDocument
from app.database.models.agent import AgentRun, ToolCall
from app.database.models.evidence import Hypothesis, EvidenceRecord, EvidenceLink
from app.database.models.approval import Report
from app.database.repositories.investigation_repository import InvestigationRepository
from app.database.repositories.client_repository import ClientRepository
from app.database.repositories.audit_repository import AuditRepository
from app.database.repositories.user_repository import UserRepository
from app.config.security import decode_access_token
from app.schemas.investigation import InvestigationCreate, InvestigationResponse, InvestigationUpdate, NoticeResponse
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.schemas.evidence import HypothesisResponse, EvidenceRecordResponse
from app.schemas.agent import AgentRunResponse, ToolCallResponse
from app.schemas.approval import ReportResponse
from app.core.dependencies import get_current_user, require_auditor, require_accountant
from app.workflows.graph import workflow_graph
from app.workflows.state import InvestigationWorkflowState
from app.investigation.stream_manager import stream_manager
from app.config.logging import get_logger

logger = get_logger("investigations_endpoint")
router = APIRouter()

@router.get("", response_model=PaginatedResponse[InvestigationResponse])
async def list_investigations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = InvestigationRepository(db)
    skip = (page - 1) * page_size
    invs = await repo.list_by_organization(
        str(current_user.organization_id),
        skip=skip,
        limit=page_size,
        status=status_filter,
        client_id=client_id
    )
    total = await repo.count_by_organization(
        str(current_user.organization_id),
        status=status_filter,
        client_id=client_id
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    responses = []
    for inv in invs:
        notice_resp = None
        if inv.notice:
            notice_resp = NoticeResponse(
                id=str(inv.notice.id),
                investigation_id=str(inv.notice.investigation_id),
                notice_number=inv.notice.notice_number,
                notice_type=inv.notice.notice_type,
                gstin=inv.notice.gstin,
                tax_period=inv.notice.tax_period,
                itc_claimed=float(inv.notice.itc_claimed) if inv.notice.itc_claimed is not None else None,
                itc_available=float(inv.notice.itc_available) if inv.notice.itc_available is not None else None,
                itc_mismatch=float(inv.notice.itc_mismatch) if inv.notice.itc_mismatch is not None else None,
                response_deadline=inv.notice.response_deadline,
                issued_date=inv.notice.issued_date,
                issuing_authority=inv.notice.issuing_authority,
                extraction_confidence=float(inv.notice.extraction_confidence) if inv.notice.extraction_confidence is not None else None,
                status=inv.notice.status
            )
        d_str = str(inv.response_deadline) if inv.response_deadline else (str(inv.notice.response_deadline) if inv.notice and inv.notice.response_deadline else None)
        from app.workflows.nodes import _compute_deadline_urgency
        d_info = _compute_deadline_urgency(d_str)
        responses.append(InvestigationResponse(
            id=str(inv.id),
            organization_id=str(inv.organization_id),
            client_id=str(inv.client_id),
            title=inv.title,
            description=inv.description,
            status=inv.status,
            mismatch_amount=float(inv.mismatch_amount) if inv.mismatch_amount else None,
            tax_period=inv.tax_period,
            response_deadline=inv.response_deadline,
            days_remaining=d_info["deadline_days_remaining"],
            is_overdue=d_info["is_overdue"],
            deadline_urgency=d_info["deadline_urgency"],
            is_demo=inv.is_demo,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            client_business_name=inv.client.business_name if inv.client else None,
            client_gstin=inv.client.primary_gstin if inv.client else None,
            notice=notice_resp
        ))

    return PaginatedResponse(
        success=True,
        data=responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("", response_model=SuccessResponse[InvestigationResponse], status_code=status.HTTP_201_CREATED)
async def create_investigation(
    inv_in: InvestigationCreate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    client_repo = ClientRepository(db)
    client = await client_repo.get_by_id(inv_in.client_id)
    if not client or str(client.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Client not found in your organization")

    repo = InvestigationRepository(db)
    if inv_in.idempotency_key:
        existing = await repo.get_by_idempotency_key(inv_in.idempotency_key)
        if existing:
            return SuccessResponse(
                data=InvestigationResponse(
                    id=str(existing.id),
                    organization_id=str(existing.organization_id),
                    client_id=str(existing.client_id),
                    title=existing.title,
                    description=existing.description,
                    status=existing.status,
                    mismatch_amount=float(existing.mismatch_amount) if existing.mismatch_amount else None,
                    tax_period=existing.tax_period,
                    response_deadline=existing.response_deadline,
                    is_demo=existing.is_demo,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at,
                    client_business_name=client.business_name,
                    client_gstin=client.primary_gstin
                ),
                message="Retrieved existing investigation by idempotency key"
            )

    inv_id = uuid.uuid4()
    inv = Investigation(
        id=inv_id,
        organization_id=current_user.organization_id,
        client_id=uuid.UUID(inv_in.client_id) if isinstance(inv_in.client_id, str) else inv_in.client_id,
        created_by_id=current_user.id,
        title=inv_in.title,
        description=inv_in.description,
        tax_period=inv_in.tax_period,
        mismatch_amount=inv_in.mismatch_amount,
        response_deadline=inv_in.response_deadline,
        status="PENDING",
        is_demo=client.is_demo,
        idempotency_key=inv_in.idempotency_key
    )
    db.add(inv)
    await db.commit()

    d_str = str(inv.response_deadline) if inv.response_deadline else (str(inv.notice.response_deadline) if inv.notice and inv.notice.response_deadline else None)
    from app.workflows.nodes import _compute_deadline_urgency
    d_info = _compute_deadline_urgency(d_str)

    return SuccessResponse(
        data=InvestigationResponse(
            id=str(inv.id),
            organization_id=str(inv.organization_id),
            client_id=str(inv.client_id),
            title=inv.title,
            description=inv.description,
            status=inv.status,
            mismatch_amount=float(inv.mismatch_amount) if inv.mismatch_amount else None,
            tax_period=inv.tax_period,
            response_deadline=inv.response_deadline,
            days_remaining=d_info["deadline_days_remaining"],
            is_overdue=d_info["is_overdue"],
            deadline_urgency=d_info["deadline_urgency"],
            is_demo=inv.is_demo,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            client_business_name=client.business_name,
            client_gstin=client.primary_gstin
        ),
        message="Investigation created successfully"
    )

@router.get("/{investigation_id}", response_model=SuccessResponse[InvestigationResponse])
async def get_investigation(
    investigation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = InvestigationRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    agent_runs_resp = []
    for r in (inv.agent_runs or []):
        meta = r.agent_metadata or {}
        summary = meta.get("output_summary") or meta.get("summary") or meta.get("task_desc")
        t_calls = [
            ToolCallResponse(
                id=str(tc.id),
                tool_name=tc.tool_name,
                mcp_server=tc.mcp_server,
                arguments=tc.arguments,
                result_summary=tc.result_summary,
                result_status=tc.result_status,
                duration_ms=tc.duration_ms,
                retry_count=tc.retry_count,
                error_message=tc.error_message,
                called_at=tc.called_at
            ) for tc in (r.tool_calls or [])
        ]
        agent_runs_resp.append(AgentRunResponse(
            id=str(r.id),
            investigation_id=str(r.investigation_id),
            agent_name=r.agent_name,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            duration_ms=r.duration_ms,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            estimated_cost_usd=float(r.estimated_cost_usd) if r.estimated_cost_usd else None,
            retry_count=r.retry_count,
            error_message=r.error_message,
            agent_metadata=r.agent_metadata,
            summary=summary,
            tool_calls=t_calls
        ))

    notice_resp = None
    if inv.notice:
        notice_resp = NoticeResponse(
            id=str(inv.notice.id),
            investigation_id=str(inv.notice.investigation_id),
            notice_number=inv.notice.notice_number,
            notice_type=inv.notice.notice_type,
            gstin=inv.notice.gstin,
            tax_period=inv.notice.tax_period,
            itc_claimed=float(inv.notice.itc_claimed) if inv.notice.itc_claimed is not None else None,
            itc_available=float(inv.notice.itc_available) if inv.notice.itc_available is not None else None,
            itc_mismatch=float(inv.notice.itc_mismatch) if inv.notice.itc_mismatch is not None else None,
            response_deadline=inv.notice.response_deadline,
            issued_date=inv.notice.issued_date,
            issuing_authority=inv.notice.issuing_authority,
            extraction_confidence=float(inv.notice.extraction_confidence) if inv.notice.extraction_confidence is not None else None,
            status=inv.notice.status
        )

    d_str = str(inv.response_deadline) if inv.response_deadline else (str(inv.notice.response_deadline) if inv.notice and inv.notice.response_deadline else None)
    from app.workflows.nodes import _compute_deadline_urgency
    d_info = _compute_deadline_urgency(d_str)

    return SuccessResponse(
        data=InvestigationResponse(
            id=str(inv.id),
            organization_id=str(inv.organization_id),
            client_id=str(inv.client_id),
            title=inv.title,
            description=inv.description,
            status=inv.status,
            mismatch_amount=float(inv.mismatch_amount) if inv.mismatch_amount else None,
            tax_period=inv.tax_period,
            response_deadline=inv.response_deadline,
            days_remaining=d_info["deadline_days_remaining"],
            is_overdue=d_info["is_overdue"],
            deadline_urgency=d_info["deadline_urgency"],
            is_demo=inv.is_demo,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            client_business_name=inv.client.business_name if inv.client else None,
            client_gstin=inv.client.primary_gstin if inv.client else None,
            notice=notice_resp,
            workflow_state=inv.workflow_state,
            agent_runs=agent_runs_resp
        )
    )

@router.post("/{investigation_id}/notice")
async def upload_notice_text(
    investigation_id: str,
    notice_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    repo = InvestigationRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    extracted_text = notice_text or ""
    if file:
        content = await file.read()
        extracted_text = content.decode("utf-8", errors="ignore")

    if not extracted_text:
        extracted_text = "FORM GST DRC-01A\nNotice ZA271223001928K\nGSTIN: 27AABCT1234C1Z5\nTax Period: 2023-11\nExcess ITC: INR 81,000.00"

    doc = UploadedDocument(
        id=uuid.uuid4(),
        investigation_id=inv.id,
        uploaded_by_id=current_user.id,
        filename=file.filename if file else "notice_text_entry.txt",
        original_filename=file.filename if file else "notice_text_entry.txt",
        file_path="memory://uploaded_notice",
        document_type="NOTICE",
        processing_status="EXTRACTED",
        extracted_text=extracted_text
    )
    db.add(doc)
    await db.commit()

    return SuccessResponse(
        data={"investigation_id": investigation_id, "text_length": len(extracted_text)},
        message="Notice text uploaded successfully"
    )

@router.post("/{investigation_id}/run")
async def run_investigation_workflow(
    investigation_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    repo = InvestigationRepository(db)
    audit_repo = AuditRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    # Phase 5: Idempotency — if same Idempotency-Key already ran, return existing result
    if idempotency_key and inv.idempotency_key == idempotency_key:
        logger.info("run_investigation_idempotent_hit", investigation_id=investigation_id, key=idempotency_key)
        wf = inv.workflow_state or {}
        return SuccessResponse(
            data={
                "investigation_id": str(inv.id),
                "status": inv.status,
                "idempotent": True,
                "verification_passed": wf.get("verification_passed", False),
                "approval_required": wf.get("approval_required", False),
                "hypotheses_count": len(wf.get("evaluated_hypotheses", [])),
                "suspect_invoices_count": len(wf.get("suspect_invoices", [])),
                "mismatch_items_count": len(wf.get("mismatch_items", [])),
            },
            message="Investigation already executed for this idempotency key"
        )

    # Phase 5: Idempotency — concurrent double-click guard via status
    active_statuses = {"INVESTIGATING", "CHALLENGING_EVIDENCE", "VERIFYING"}
    if inv.status in active_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"AI investigation is already running (current status: {inv.status})."
        )

    allowed_start_statuses = {
        "PENDING",
        "PARSING_NOTICE",
        "VALIDATING_NOTICE",
        "BUILDING_PLAN",
        "NEEDS_MORE_EVIDENCE",
    }
    if inv.status not in allowed_start_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start AI investigation from status '{inv.status}'."
        )

    if idempotency_key:
        inv.idempotency_key = idempotency_key
    inv.status = "INVESTIGATING"
    await db.commit()

    # Phase 7: Audit trail — log investigation start
    await audit_repo.log_action(
        action="INVESTIGATION_STARTED",
        resource_type="investigation",
        resource_id=str(inv.id),
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        details={"title": inv.title, "client_id": str(inv.client_id)}
    )
    await db.commit()

    # Get notice text from uploaded documents or default demo notice
    notice_text = ""
    if inv.documents:
        notice_text = inv.documents[0].extracted_text or ""
    if not notice_text:
        notice_text = (
            "FORM GST DRC-01A [See Rule 142(1A)]\n"
            "Notice Number: ZA271223001928K\n"
            "Taxpayer GSTIN: 27AABCT1234C1Z5\n"
            "Tax Period: 2023-11\n"
            "ITC Claimed in GSTR-3B: INR 1,74,600.00\n"
            "ITC Available in GSTR-2B: INR 93,600.00\n"
            "Excess ITC Claimed: INR 81,000.00\n"
            "Response Deadline: 2024-01-15\n"
        )

    client_name = inv.client.business_name if inv.client else "ABC Traders Pvt Ltd"
    client_gstin = inv.client.primary_gstin if inv.client else "27AABCT1234C1Z5"

    initial_state: InvestigationWorkflowState = {
        "investigation_id": str(inv.id),
        "organization_id": str(inv.organization_id),
        "client_id": str(inv.client_id),
        "client_name": client_name,
        "client_gstin": client_gstin,
        "notice_text": notice_text
    }

    # Execute workflow graph (halts at ACCOUNTANT_APPROVAL for human-in-the-loop)
    result_state = await workflow_graph.run(initial_state)

    # Persist findings & agent runs to database
    inv.status = "AWAITING_APPROVAL" if result_state.get("approval_required") else "INVESTIGATING"
    inv.workflow_state = result_state
    inv.mismatch_amount = result_state.get("notice_data", {}).get("itc_mismatch", inv.mismatch_amount)
    inv.tax_period = result_state.get("notice_data", {}).get("tax_period", inv.tax_period)

    # Phase 3: Persist deadline from parsed notice
    parsed_deadline = result_state.get("response_deadline") or result_state.get("notice_data", {}).get("response_deadline")
    if parsed_deadline and not inv.response_deadline:
        try:
            from datetime import date as _date
            inv.response_deadline = _date.fromisoformat(str(parsed_deadline)[:10])
        except ValueError:
            pass

    # Save Hypotheses
    eval_hyps = result_state.get("evaluated_hypotheses", [])
    for h in eval_hyps:
        hyp = Hypothesis(
            id=uuid.uuid4(),
            investigation_id=inv.id,
            hypothesis_type=h.get("hypothesis_type", "OTHER"),
            title=h.get("title", "Hypothesis"),
            status=h.get("status", "UNVERIFIED"),
            confidence_score=h.get("final_confidence", 0.5),
            supporting_evidence_count=len(h.get("supporting_evidence_ids", [])),
            contradicting_evidence_count=len(h.get("contradicting_evidence_ids", [])),
            challenge_rationale=h.get("challenge_rationale")
        )
        db.add(hyp)

    # Save Evidence Records
    for inv_rec in result_state.get("suspect_invoices", []):
        ev = EvidenceRecord(
            id=uuid.uuid4(),
            investigation_id=inv.id,
            source_id=inv_rec.get("source_id", "SRC-INV"),
            source_type="INVOICE",
            document_name=f"Tax Invoice {inv_rec.get('invoice_number')}",
            amount=inv_rec.get("tax_amount"),
            tax_period=inv.tax_period,
            gstin=inv_rec.get("supplier_gstin"),
            status="SUPPORTED",
            retrieved_by="Ledger Matcher Agent",
            mcp_server="ledger_mcp"
        )
        db.add(ev)

    # Save Draft Report if generated
    if result_state.get("response_draft"):
        await db.execute(
            update(Report)
            .where(Report.investigation_id == inv.id)
            .values(is_latest=False)
        )
        draft_data = result_state.get("response_draft")
        db.add(Report(
            id=uuid.uuid4(),
            investigation_id=inv.id,
            report_type="RESPONSE_DRAFT",
            title=draft_data.get("title") or f"Response Draft — {inv.title}",
            content=draft_data,
            is_latest=True,
            generated_by="Response Drafter Agent"
        ))

    # Phase 7: Audit trail — log investigation completion
    await audit_repo.log_action(
        action="INVESTIGATION_COMPLETED",
        resource_type="investigation",
        resource_id=str(inv.id),
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        details={
            "final_status": inv.status,
            "hypotheses_count": len(eval_hyps),
            "mismatch_items_count": len(result_state.get("mismatch_items", [])),
            "verification_passed": result_state.get("verification_passed", False),
            "deadline_urgency": result_state.get("deadline_urgency"),
        }
    )

    await db.commit()

    return SuccessResponse(
        data={
            "investigation_id": str(inv.id),
            "status": inv.status,
            "verification_passed": result_state.get("verification_passed", False),
            "approval_required": result_state.get("approval_required", False),
            "hypotheses_count": len(eval_hyps),
            "suspect_invoices_count": len(result_state.get("suspect_invoices", [])),
            "mismatch_items_count": len(result_state.get("mismatch_items", [])),
            "deadline_urgency": result_state.get("deadline_urgency"),
            "days_remaining": result_state.get("deadline_days_remaining"),
        },
        message="Multi-agent investigation executed successfully"
    )

@router.get("/{investigation_id}/events")
@router.get("/{investigation_id}/stream")
async def stream_investigation_events(
    investigation_id: str,
    token: Optional[str] = Query(None),
    replay_only: bool = Query(False, description="Replay buffered history and terminate stream"),
    timeout: Optional[float] = Query(None, description="Max stream duration in seconds"),
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events (SSE) live telemetry stream.
    Streams real-time agent execution events, MCP tool calls, and state transitions.
    """
    if token:
        try:
            payload = decode_access_token(token)
            if payload and payload.get("sub"):
                user_repo = UserRepository(db)
                user = await user_repo.get_by_id(payload["sub"])
                inv_repo = InvestigationRepository(db)
                inv = await inv_repo.get_by_id(investigation_id)
                if user and inv and str(inv.organization_id) != str(user.organization_id):
                    raise HTTPException(status_code=403, detail="Forbidden")
        except HTTPException:
            raise
        except Exception:
            pass

    return StreamingResponse(
        stream_manager.subscribe(investigation_id, replay_only=replay_only, timeout=timeout),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/{investigation_id}/evidence", response_model=SuccessResponse[Dict[str, Any]])
async def get_investigation_evidence(
    investigation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = InvestigationRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    hyps_res = [
        HypothesisResponse(
            id=str(h.id),
            investigation_id=str(h.investigation_id),
            hypothesis_type=h.hypothesis_type,
            title=h.title,
            description=h.description,
            status=h.status,
            confidence_score=h.confidence_score,
            supporting_evidence_count=int(h.supporting_evidence_count or 0),
            contradicting_evidence_count=int(h.contradicting_evidence_count or 0),
            missing_evidence_description=h.missing_evidence_description,
            investigator_rationale=h.investigator_rationale,
            challenge_rationale=h.challenge_rationale,
            created_at=h.created_at,
            evidence_records=[]
        )
        for h in (inv.hypotheses or [])
    ]

    records_res = [
        EvidenceRecordResponse(
            id=str(r.id),
            investigation_id=str(r.investigation_id),
            source_id=r.source_id,
            source_type=r.source_type,
            document_name=r.document_name,
            amount=float(r.amount) if r.amount else None,
            tax_period=r.tax_period,
            gstin=r.gstin,
            retrieved_at=r.retrieved_at,
            retrieved_by=r.retrieved_by,
            mcp_server=r.mcp_server,
            status=r.status,
            verification_notes=r.verification_notes
        )
        for r in (inv.evidence_records or [])
    ]

    return SuccessResponse(data={"hypotheses": hyps_res, "evidence_records": records_res})

@router.get("/{investigation_id}/agents", response_model=SuccessResponse[List[AgentRunResponse]])
async def get_investigation_agents(
    investigation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = InvestigationRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    runs = []
    for r in (inv.agent_runs or []):
        tool_calls = [
            {
                "id": str(t.id),
                "tool_name": t.tool_name,
                "mcp_server": t.mcp_server,
                "arguments": t.arguments,
                "result_status": t.result_status,
                "duration_ms": t.duration_ms,
                "retry_count": t.retry_count,
                "called_at": t.called_at
            }
            for t in (r.tool_calls or [])
        ]
        runs.append(AgentRunResponse(
            id=str(r.id),
            investigation_id=str(r.investigation_id),
            agent_name=r.agent_name,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            duration_ms=r.duration_ms,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            estimated_cost_usd=float(r.estimated_cost_usd) if r.estimated_cost_usd else None,
            retry_count=r.retry_count,
            error_message=r.error_message,
            agent_metadata=r.agent_metadata,
            tool_calls=tool_calls
        ))

    return SuccessResponse(data=runs)

@router.get("/{investigation_id}/report", response_model=SuccessResponse[Optional[ReportResponse]])
async def get_investigation_report(
    investigation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = InvestigationRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    report = next((r for r in (inv.reports or []) if r.is_latest), None)
    if not report:
        return SuccessResponse(data=None, message="No report generated yet")

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


# ---------------------------------------------------------------------------
# Phase 3: Deadline Tracking — PATCH /investigations/{id}/deadline
# ---------------------------------------------------------------------------

from pydantic import BaseModel as PydanticBaseModel

class DeadlineUpdateRequest(PydanticBaseModel):
    response_deadline: str   # ISO date YYYY-MM-DD
    notes: Optional[str] = None


@router.patch("/{investigation_id}/deadline", response_model=SuccessResponse[Dict[str, Any]])
async def update_investigation_deadline(
    investigation_id: str,
    body: DeadlineUpdateRequest,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    """
    Auditor can manually update the GST notice response deadline.
    Records an audit log entry for traceability.
    """
    from datetime import date as _date
    from app.workflows.nodes import _compute_deadline_urgency  # noqa: local import

    repo = InvestigationRepository(db)
    audit_repo = AuditRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    # Validate date format
    try:
        parsed_date_obj = _date.fromisoformat(body.response_deadline)
    except ValueError:
        raise HTTPException(status_code=400, detail="response_deadline must be YYYY-MM-DD")

    old_deadline = inv.response_deadline
    inv.response_deadline = parsed_date_obj
    await db.commit()

    urgency_info = _compute_deadline_urgency(body.response_deadline)

    # Audit log
    await audit_repo.log_action(
        action="DEADLINE_UPDATED",
        resource_type="investigation",
        resource_id=str(inv.id),
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        details={
            "old_deadline": str(old_deadline) if old_deadline else None,
            "new_deadline": body.response_deadline,
            "notes": body.notes,
        }
    )
    await db.commit()

    return SuccessResponse(
        data={
            "investigation_id": str(inv.id),
            "response_deadline": body.response_deadline,
            "days_remaining": urgency_info["deadline_days_remaining"],
            "is_overdue": urgency_info["is_overdue"],
            "urgency": urgency_info["deadline_urgency"],
        },
        message="Deadline updated successfully"
    )


# ---------------------------------------------------------------------------
# Phase 3: Deadline summary — GET /investigations/deadlines
# ---------------------------------------------------------------------------

@router.get("/deadlines/at-risk", response_model=SuccessResponse[List[Dict[str, Any]]])
async def get_at_risk_deadlines(
    urgency: Optional[str] = Query(None, description="Filter: CRITICAL|HIGH|MEDIUM|LOW"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns investigations with upcoming or overdue deadlines for Auditor dashboard.
    Urgency levels: CRITICAL (<3 days or overdue) | HIGH (<7 days) | MEDIUM (<14 days) | LOW.
    """
    from app.workflows.nodes import _compute_deadline_urgency  # noqa: local import

    repo = InvestigationRepository(db)
    all_invs = await repo.list_by_organization(
        str(current_user.organization_id),
        skip=0,
        limit=200,
        status=None
    )

    result = []
    for inv in all_invs:
        if not inv.response_deadline:
            continue
        d_info = _compute_deadline_urgency(str(inv.response_deadline))
        if urgency and d_info["deadline_urgency"] != urgency:
            continue
        if d_info["deadline_urgency"] == "NONE":
            continue
        result.append({
            "investigation_id": str(inv.id),
            "title": inv.title,
            "status": inv.status,
            "client_name": inv.client.business_name if inv.client else None,
            "client_gstin": inv.client.primary_gstin if inv.client else None,
            "response_deadline": str(inv.response_deadline),
            "days_remaining": d_info["deadline_days_remaining"],
            "is_overdue": d_info["is_overdue"],
            "urgency": d_info["deadline_urgency"],
        })

    # Sort: overdue first, then soonest
    result.sort(key=lambda x: (not x["is_overdue"], x["days_remaining"] if x["days_remaining"] is not None else 9999))

    return SuccessResponse(data=result, message=f"{len(result)} investigations with deadline risk")
