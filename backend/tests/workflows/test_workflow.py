import pytest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.workflows.graph import workflow_graph
from app.workflows.state import InvestigationWorkflowState

SAMPLE_NOTICE_TEXT = """
FORM GST DRC-01A
Notice Number: ZA271223001928K
Taxpayer GSTIN: 27AABCT1234C1Z5
Tax Period: 2023-11
Excess ITC claimed: INR 81,000.00
Response Deadline: 2024-01-15
"""

@pytest.mark.asyncio
async def test_workflow_runs_and_pauses_at_approval():
    initial_state: InvestigationWorkflowState = {
        "investigation_id": "WF-TEST-001",
        "client_name": "ABC Traders Pvt Ltd",
        "client_gstin": "27AABCT1234C1Z5",
        "notice_text": SAMPLE_NOTICE_TEXT
    }

    final_state = await workflow_graph.run(initial_state)

    # Verify workflow executed through all nodes up to ACCOUNTANT_APPROVAL
    history = final_state.get("step_history", [])
    assert "LOAD_INVESTIGATION" in history
    assert "PARSE_NOTICE" in history
    assert "VALIDATE_NOTICE" in history
    assert "BUILD_INVESTIGATION_PLAN" in history
    assert "CREATE_INVOICE_TASKS" in history
    assert "LEDGER_INVESTIGATION" in history
    assert "ROOT_CAUSE_INVESTIGATION" in history
    assert "EVIDENCE_CHALLENGE" in history
    assert "VERIFICATION_GATE" in history
    assert "RESPONSE_DRAFTING" in history
    assert "ACCOUNTANT_APPROVAL" in history

    # Verify paused at approval gate
    assert final_state["current_node"] == "ACCOUNTANT_APPROVAL"
    assert final_state["approval_required"] is True
    assert final_state["response_draft"] is not None
    assert final_state.get("checkpoint_id") is not None

@pytest.mark.asyncio
async def test_workflow_conditional_routing_on_invalid_notice():
    invalid_state: InvestigationWorkflowState = {
        "investigation_id": "WF-INVALID-001",
        "client_name": "ABC Traders Pvt Ltd",
        "client_gstin": "27AABCT1234C1Z5",
        "notice_text": "Non-tax random letter without any GST details or amounts."
    }

    result = await workflow_graph.run(invalid_state)
    assert result["current_node"] == "VALIDATE_NOTICE"
    assert result["notice_valid"] is False
    assert "BUILD_INVESTIGATION_PLAN" not in result.get("step_history", [])
