import pytest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.agents.notice_parser import NoticeParserAgent
from app.agents.ledger_matcher import LedgerMatcherAgent
from app.agents.root_cause_investigator import RootCauseInvestigatorAgent
from app.agents.evidence_challenge import EvidenceChallengeEngine
from app.investigation.verification_gate import verification_gate
from app.agents.response_drafter import ResponseDrafterAgent
from app.agents.supervisor import supervisor_agent

SAMPLE_NOTICE_TEXT = """
FORM GST DRC-01A
[See Rule 142(1A)]
Intimation of tax ascertained as payable through notice.
Notice Number: ZA271223001928K
Taxpayer GSTIN: 27AABCT1234C1Z5
Legal Name: ABC Traders Pvt Ltd
Tax Period: 2023-11
Summary of Discrepancy:
Input Tax Credit (ITC) claimed in GSTR-3B: INR 1,74,600.00
Input Tax Credit (ITC) available in GSTR-2B: INR 93,600.00
Excess ITC claimed: INR 81,000.00 (CGST: 40,500.00, SGST: 40,500.00)
Response Deadline: 2024-01-15
"""

@pytest.mark.asyncio
async def test_notice_parser_agent():
    parser = NoticeParserAgent()
    data = await parser.parse_text(SAMPLE_NOTICE_TEXT)
    assert data.notice_number == "ZA271223001928K"
    assert data.gstin == "27AABCT1234C1Z5"
    assert data.itc_mismatch == 81000.0
    assert data.itc_claimed == 174600.0

@pytest.mark.asyncio
async def test_ledger_matcher_react_loop():
    matcher = LedgerMatcherAgent()
    log = await matcher.investigate_ledger(
        investigation_id="TEST-INV-001",
        client_gstin="27AABCT1234C1Z5",
        tax_period="2023-11",
        mismatch_amount=81000.0
    )
    assert log.total_iterations >= 1
    assert log.tool_calls_count >= 1
    invoices = log.final_data.get("matched_invoices", [])
    assert len(invoices) >= 1
    assert invoices[0]["tax_amount"] == 81000.0

@pytest.mark.asyncio
async def test_root_cause_investigator_react_loop():
    rc = RootCauseInvestigatorAgent()
    suspect = [{"invoice_number": "INV-2023-0891", "supplier_gstin": "27AABCS5555D1Z8"}]
    log = await rc.investigate_root_causes(
        investigation_id="TEST-INV-001",
        client_gstin="27AABCT1234C1Z5",
        tax_period="2023-11",
        mismatch_amount=81000.0,
        suspect_invoices=suspect
    )
    assert log.total_iterations >= 2
    hypotheses = log.final_data.get("hypotheses", [])
    assert len(hypotheses) >= 2
    assert any(h["hypothesis_type"] == "TIMING_DIFFERENCE" for h in hypotheses)

@pytest.mark.asyncio
async def test_evidence_challenge_engine_react_loop():
    engine = EvidenceChallengeEngine()
    hypotheses = [
        {
            "hypothesis_type": "TIMING_DIFFERENCE",
            "title": "Supplier GSTR-1 Filed in Subsequent Tax Period",
            "initial_confidence": 0.95
        },
        {
            "hypothesis_type": "DUPLICATE_INVOICE",
            "title": "Potential Duplicate Credit Availment",
            "initial_confidence": 0.15
        }
    ]
    log = await engine.challenge_hypotheses(
        investigation_id="TEST-INV-001",
        client_gstin="27AABCT1234C1Z5",
        tax_period="2023-11",
        mismatch_amount=81000.0,
        proposed_hypotheses=hypotheses
    )
    evaluated = log.final_data.get("evaluated_hypotheses", [])
    assert len(evaluated) == 2
    timing_hyp = next(h for h in evaluated if h["hypothesis_type"] == "TIMING_DIFFERENCE")
    assert timing_hyp["status"] == "SUPPORTED"
    dup_hyp = next(h for h in evaluated if h["hypothesis_type"] == "DUPLICATE_INVOICE")
    assert dup_hyp["status"] == "CONTRADICTED"

def test_deterministic_verification_gate():
    suspect_invoices = [{"invoice_number": "INV-2023-0891", "tax_amount": 81000.0}]
    evaluated_hypotheses = [
        {
            "hypothesis_type": "TIMING_DIFFERENCE",
            "title": "Timing Difference",
            "status": "SUPPORTED",
            "supporting_evidence_ids": ["SRC-INV-0891", "SRC-VEN-STATUS"],
            "challenge_rationale": "Tax discharged to government in subsequent period"
        },
        {
            "hypothesis_type": "DUPLICATE_INVOICE",
            "title": "Duplicate",
            "status": "CONTRADICTED",
            "contradicting_evidence_ids": ["SRC-LED-SINGLE"],
            "challenge_rationale": "Only single ledger entry found"
        }
    ]
    gate_res = verification_gate.verify_investigation(
        notice_mismatch_amount=81000.0,
        suspect_invoices=suspect_invoices,
        evaluated_hypotheses=evaluated_hypotheses
    )
    assert gate_res.is_approved is True
    assert gate_res.verdict == "SUPPORTED"
    assert len(gate_res.verified_findings) == 1
    assert len(gate_res.rejected_hypotheses) == 1

@pytest.mark.asyncio
async def test_end_to_end_supervisor_investigation():
    result = await supervisor_agent.run_investigation(
        investigation_id="E2E-TEST-001",
        client_name="ABC Traders Pvt Ltd",
        client_gstin="27AABCT1234C1Z5",
        notice_text=SAMPLE_NOTICE_TEXT
    )
    assert result.status == "AWAITING_APPROVAL"
    assert result.verification_result.is_approved is True
    assert result.response_draft is not None
    assert result.response_draft.requires_human_approval is True
    assert "Section 16(2)" in result.response_draft.legal_submissions
