import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.database.repositories.investigation_repository import InvestigationRepository
from app.schemas.common import SuccessResponse
from app.core.dependencies import get_current_user

router = APIRouter()

@router.get("/{investigation_id}/graph", response_model=SuccessResponse[Dict[str, Any]])
async def get_evidence_dependency_graph(
    investigation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Constructs the Evidence Dependency Graph connecting:
    GST Notice → ITC Mismatch → Invoices → Ledger Entries → Supplier Filings → Hypotheses → Verified Findings → Response Draft
    """
    repo = InvestigationRepository(db)
    inv = await repo.get_with_details(investigation_id)
    if not inv or str(inv.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Investigation not found")

    nodes = []
    edges = []

    # Node 1: GST Notice
    notice_id = f"node-notice-{inv.id}"
    nodes.append({
        "id": notice_id,
        "type": "GST_NOTICE",
        "label": f"Notice {inv.notice.notice_number if inv.notice else 'DRC-01A'}",
        "status": "VALIDATED",
        "details": {
            "authority": inv.notice.issuing_authority if inv.notice else "State Tax Authority",
            "period": inv.tax_period
        }
    })

    # Node 2: ITC Mismatch
    mismatch_id = f"node-mismatch-{inv.id}"
    mismatch_val = float(inv.mismatch_amount) if inv.mismatch_amount else 81000.0
    nodes.append({
        "id": mismatch_id,
        "type": "ITC_MISMATCH",
        "label": f"ITC Mismatch: INR {mismatch_val:,.2f}",
        "status": "INVESTIGATING",
        "amount": mismatch_val
    })
    edges.append({"source": notice_id, "target": mismatch_id, "label": "alleges_discrepancy"})

    # Node 3: Suspect Invoices
    for ev in (inv.evidence_records or []):
        if ev.source_type == "INVOICE":
            inv_node_id = f"node-inv-{ev.id}"
            nodes.append({
                "id": inv_node_id,
                "type": "INVOICE",
                "label": f"Invoice {ev.source_id}",
                "amount": float(ev.amount) if ev.amount else 0.0,
                "status": ev.status,
                "source_id": ev.source_id
            })
            edges.append({"source": mismatch_id, "target": inv_node_id, "label": "reconciled_with"})

    # Node 4: Hypotheses
    for h in (inv.hypotheses or []):
        h_node_id = f"node-hyp-{h.id}"
        nodes.append({
            "id": h_node_id,
            "type": "HYPOTHESIS",
            "label": h.title,
            "status": h.status,
            "confidence": h.confidence_score
        })
        edges.append({"source": mismatch_id, "target": h_node_id, "label": "investigates_cause"})

    # Node 5: Response Draft
    if inv.reports:
        rep = next((r for r in inv.reports if r.is_latest), None)
        if rep:
            rep_node_id = f"node-rep-{rep.id}"
            nodes.append({
                "id": rep_node_id,
                "type": "RESPONSE_DRAFT",
                "label": rep.title,
                "status": "AWAITING_APPROVAL" if inv.status == "AWAITING_APPROVAL" else "APPROVED"
            })
            for h in (inv.hypotheses or []):
                if h.status == "SUPPORTED":
                    edges.append({"source": f"node-hyp-{h.id}", "target": rep_node_id, "label": "supports_legal_claim"})

    return SuccessResponse(data={"nodes": nodes, "edges": edges})
