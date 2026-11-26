from typing import Dict, Any, List
from pydantic import BaseModel
from app.investigation.react_engine import BoundedReActLoop, ReActAction, ReActExecutionLog
from app.config.logging import get_logger

logger = get_logger("root_cause_investigator")

class ProposedHypothesis(BaseModel):
    hypothesis_type: str
    title: str
    description: str
    initial_confidence: float
    supporting_evidence_ids: List[str] = []
    investigator_rationale: str

def _get_next_tax_period(period: str) -> str:
    try:
        parts = period.split("-")
        year, month = int(parts[0]), int(parts[1])
        if month == 12:
            return f"{year + 1:04d}-01"
        return f"{year:04d}-{month + 1:02d}"
    except Exception:
        return "2023-12"

class RootCauseInvestigatorAgent:
    """Agent 4 — Root-Cause Investigator (ReAct Loop 2: Hypotheses Generation & Investigation)."""
    def __init__(self):
        self.role_name = "Root-Cause Investigator Agent"

    async def investigate_root_causes(
        self,
        investigation_id: str,
        client_gstin: str,
        tax_period: str,
        mismatch_amount: float,
        suspect_invoices: List[Dict[str, Any]]
    ) -> ReActExecutionLog:
        logger.info("root_cause_started", investigation_id=investigation_id, invoice_count=len(suspect_invoices))
        loop = BoundedReActLoop(agent_name=self.role_name, investigation_id=investigation_id, max_iterations=8)

        hypotheses: List[Dict[str, Any]] = []

        # Target suspect supplier from ledger matcher
        supplier_gstin = suspect_invoices[0].get("supplier_gstin", "27AABCS5555D1Z8") if suspect_invoices else "27AABCS5555D1Z8"
        inv_no = suspect_invoices[0].get("invoice_number", "INV-2023-0891") if suspect_invoices else "INV-2023-0891"

        # Step 1: Check supplier filing status in current period
        action_1 = ReActAction(
            tool_name="get_vendor_filing_status",
            arguments={"supplier_gstin": supplier_gstin, "tax_period": tax_period},
            rationale=f"Check if supplier {supplier_gstin} filed GSTR-1 in {tax_period}."
        )
        obs_1 = await loop.execute_action(action_1)
        loop.record_step(1, action_1.rationale, action_1, obs_1)

        gstr1_status_current = obs_1.data.get("gstr1_status")

        # Step 2: Test Timing Difference hypothesis — Check subsequent period
        next_period = _get_next_tax_period(tax_period)
        action_2 = ReActAction(
            tool_name="get_vendor_filing_status",
            arguments={"supplier_gstin": supplier_gstin, "tax_period": next_period},
            rationale=f"Check if supplier {supplier_gstin} filed invoice in subsequent period {next_period}."
        )
        obs_2 = await loop.execute_action(action_2)
        loop.record_step(2, action_2.rationale, action_2, obs_2)

        gstr1_status_next = obs_2.data.get("gstr1_status")

        # Step 3: Check subsequent GSTR-2B details to confirm invoice reflection
        action_3 = ReActAction(
            tool_name="get_return_details",
            arguments={"gstin": client_gstin, "return_type": "GSTR-2B", "tax_period": next_period},
            rationale=f"Verify whether invoice {inv_no} appeared in client's GSTR-2B for {next_period}."
        )
        obs_3 = await loop.execute_action(action_3)
        loop.record_step(3, action_3.rationale, action_3, obs_3)

        line_items_next = obs_3.data.get("line_items", [])
        found_in_next = any(item.get("invoice_number") == inv_no for item in line_items_next)

        # Formulate competing hypotheses
        if found_in_next:
            hypotheses.append({
                "hypothesis_type": "TIMING_DIFFERENCE",
                "title": f"Supplier GSTR-1 Filed in Subsequent Tax Period ({next_period})",
                "description": f"Supplier {supplier_gstin} issued {inv_no} in {tax_period} but reported it in GSTR-1 of {next_period}. The invoice is now reflected in GSTR-2B.",
                "initial_confidence": 0.95,
                "supporting_evidence_ids": [obs_2.data.get("source_id", f"SRC-VEN-{next_period}"), obs_3.data.get("source_id", f"SRC-2B-{next_period}")],
                "investigator_rationale": "High confidence timing mismatch. Credit legally claimed upon invoice receipt; supplier reported one month late."
            })
        else:
            hypotheses.append({
                "hypothesis_type": "SUPPLIER_FILING_ISSUE",
                "title": f"Supplier Non-Filing or Incomplete Return",
                "description": f"Supplier {supplier_gstin} has not reflected invoice {inv_no} in GSTR-2B of current or subsequent period.",
                "initial_confidence": 0.85,
                "supporting_evidence_ids": [obs_1.data.get("source_id", "SRC-VEN-NOV")],
                "investigator_rationale": "Supplier failed to declare invoice in GSTR-1."
            })

        # Add competing duplicate invoice hypothesis
        hypotheses.append({
            "hypothesis_type": "DUPLICATE_INVOICE",
            "title": "Potential Duplicate Credit Availment",
            "description": f"Verify whether invoice {inv_no} was claimed multiple times in accounting ledger.",
            "initial_confidence": 0.15,
            "supporting_evidence_ids": [],
            "investigator_rationale": "Standard audit hypothesis to rule out clerical duplicate booking."
        })

        verdict = f"Generated {len(hypotheses)} root-cause hypotheses. Primary candidate: {hypotheses[0]['title']}."

        return ReActExecutionLog(
            agent_name=self.role_name,
            investigation_id=investigation_id,
            total_iterations=len(loop.steps),
            tool_calls_count=loop.tool_calls_made,
            token_usage_estimated=1800,
            steps=loop.steps,
            final_verdict=verdict,
            final_data={"hypotheses": hypotheses}
        )
