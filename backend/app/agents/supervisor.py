from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from app.agents.notice_parser import NoticeParserAgent, ExtractedNoticeData
from app.agents.ledger_matcher import LedgerMatcherAgent
from app.agents.root_cause_investigator import RootCauseInvestigatorAgent
from app.agents.evidence_challenge import EvidenceChallengeEngine
from app.investigation.verification_gate import verification_gate, VerificationGateResult
from app.agents.response_drafter import ResponseDrafterAgent, ResponseDraft
from app.config.logging import get_logger

logger = get_logger("supervisor_agent")

class InvestigationPlan(BaseModel):
    plan_id: str
    investigation_id: str
    target_gstin: str
    tax_period: str
    mismatch_amount: float
    created_at: str
    tasks: List[str] = []

class EndToEndInvestigationResult(BaseModel):
    investigation_id: str
    client_name: str
    status: str
    notice_data: ExtractedNoticeData
    suspect_invoices: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    verification_result: VerificationGateResult
    response_draft: Optional[ResponseDraft] = None
    execution_logs: List[Dict[str, Any]] = []

class SupervisorAgent:
    """
    Agent 1 — Supervisor Agent.
    Master workflow controller that orchestrates the specialized worker agents.
    """
    def __init__(self):
        self.role_name = "Supervisor Agent"
        self.notice_parser = NoticeParserAgent()
        self.ledger_matcher = LedgerMatcherAgent()
        self.root_cause = RootCauseInvestigatorAgent()
        self.evidence_challenge = EvidenceChallengeEngine()
        self.response_drafter = ResponseDrafterAgent()

    async def run_investigation(
        self,
        investigation_id: str,
        client_name: str,
        client_gstin: str,
        notice_text: str
    ) -> EndToEndInvestigationResult:
        logger.info("supervisor_starting_investigation", investigation_id=investigation_id)
        execution_logs = []

        # 1. Parse Notice
        notice_data = await self.notice_parser.parse_text(notice_text)
        tax_period = notice_data.tax_period or "2023-11"
        mismatch_amt = notice_data.itc_mismatch or 81000.0

        # 2. Build Plan
        plan = InvestigationPlan(
            plan_id=f"PLAN-{investigation_id[:8]}",
            investigation_id=investigation_id,
            target_gstin=client_gstin,
            tax_period=tax_period,
            mismatch_amount=mismatch_amt,
            created_at=datetime.now(timezone.utc).isoformat(),
            tasks=[
                "Parse and validate DRC-01A notice",
                "Reconcile purchase invoices against ledger",
                "Generate competing root-cause hypotheses",
                "Run independent evidence challenge loop",
                "Pass findings through deterministic verification gate",
                "Draft structured legal response with statutory citations",
                "Submit to Chartered Accountant for human approval"
            ]
        )

        # 3. Ledger Investigation (ReAct Loop 1)
        ledger_log = await self.ledger_matcher.investigate_ledger(
            investigation_id=investigation_id,
            client_gstin=client_gstin,
            tax_period=tax_period,
            mismatch_amount=mismatch_amt
        )
        execution_logs.append(ledger_log.model_dump())
        suspect_invoices = ledger_log.final_data.get("matched_invoices", [])

        # 4. Root-Cause Investigation (ReAct Loop 2)
        rc_log = await self.root_cause.investigate_root_causes(
            investigation_id=investigation_id,
            client_gstin=client_gstin,
            tax_period=tax_period,
            mismatch_amount=mismatch_amt,
            suspect_invoices=suspect_invoices
        )
        execution_logs.append(rc_log.model_dump())
        proposed_hypotheses = rc_log.final_data.get("hypotheses", [])

        # 5. Evidence Challenge Engine (ReAct Loop 3 — Signature Differentiating Feature)
        challenge_log = await self.evidence_challenge.challenge_hypotheses(
            investigation_id=investigation_id,
            client_gstin=client_gstin,
            tax_period=tax_period,
            mismatch_amount=mismatch_amt,
            proposed_hypotheses=proposed_hypotheses
        )
        execution_logs.append(challenge_log.model_dump())
        evaluated_hypotheses = challenge_log.final_data.get("evaluated_hypotheses", [])

        # 6. Deterministic Verification Gate
        gate_result = verification_gate.verify_investigation(
            notice_mismatch_amount=mismatch_amt,
            suspect_invoices=suspect_invoices,
            evaluated_hypotheses=evaluated_hypotheses
        )

        # 7. Response Drafting (Only permitted if verification gate approves)
        response_draft = None
        final_status = "AWAITING_APPROVAL"
        if gate_result.is_approved:
            response_draft = await self.response_drafter.draft_response(
                investigation_id=investigation_id,
                client_name=client_name,
                client_gstin=client_gstin,
                notice_data=notice_data.model_dump(),
                verified_findings=gate_result.verified_findings,
                unresolved_matters=gate_result.unresolved_matters
            )
        else:
            final_status = "NEEDS_MORE_EVIDENCE"

        logger.info("supervisor_investigation_finished", status=final_status)

        return EndToEndInvestigationResult(
            investigation_id=investigation_id,
            client_name=client_name,
            status=final_status,
            notice_data=notice_data,
            suspect_invoices=suspect_invoices,
            hypotheses=evaluated_hypotheses,
            verification_result=gate_result,
            response_draft=response_draft,
            execution_logs=execution_logs
        )

supervisor_agent = SupervisorAgent()
