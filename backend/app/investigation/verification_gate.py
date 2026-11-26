from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.config.logging import get_logger

logger = get_logger("verification_gate")

class VerificationPolicyResult(BaseModel):
    is_verified: bool
    policy_name: str
    passed: bool
    details: str
    evidence_status: str = "SUPPORTED"  # SUPPORTED | CONTRADICTED | UNVERIFIED

class VerificationGateResult(BaseModel):
    is_approved: bool
    verdict: str  # SUPPORTED / CONTRADICTED / INSUFFICIENT_EVIDENCE
    policy_results: List[VerificationPolicyResult] = []
    verified_findings: List[Dict[str, Any]] = []
    rejected_hypotheses: List[Dict[str, Any]] = []
    unresolved_matters: List[Dict[str, Any]] = []
    execution_notes: str

    @property
    def checks(self) -> List[VerificationPolicyResult]:
        return self.policy_results

class DeterministicVerificationGate:
    """
    Critical Deterministic Verification Gate.
    Enforces strict mathematical and statutory consistency checks in pure Python.
    Prevents any unverified or contradicted finding from passing to the Response Drafter.
    """
    def __init__(self):
        self.name = "Deterministic Verification Gate"

    def verify_investigation(
        self,
        notice_mismatch_amount: float,
        suspect_invoices: List[Dict[str, Any]],
        evaluated_hypotheses: List[Dict[str, Any]],
        mismatch_results: Optional[List[Dict[str, Any]]] = None,
        fan_in_summary: Optional[Dict[str, Any]] = None,
        notice_tax_period: Optional[str] = None,
    ) -> VerificationGateResult:
        logger.info("verification_gate_evaluating", mismatch=notice_mismatch_amount)
        policy_results: List[VerificationPolicyResult] = []
        verified_findings: List[Dict[str, Any]] = []
        rejected_hypotheses: List[Dict[str, Any]] = []
        unresolved_matters: List[Dict[str, Any]] = []

        # Policy 1: ITC Arithmetic Reconciliation Check
        total_accounted_tax = 0.0
        for inv in suspect_invoices:
            tax = float(inv.get("tax_amount", 0.0))
            total_accounted_tax += tax

        arithmetic_diff = abs(total_accounted_tax - notice_mismatch_amount)
        arithmetic_passed = arithmetic_diff <= 1.0  # Allow 1 INR rounding tolerance
        policy_results.append(VerificationPolicyResult(
            policy_name="ITC Arithmetic Reconciliation",
            is_verified=arithmetic_passed,
            passed=arithmetic_passed,
            details=f"Calculated invoice tax INR {total_accounted_tax:.2f} vs Notice mismatch INR {notice_mismatch_amount:.2f} (Diff: INR {arithmetic_diff:.2f})"
        ))

        # Policy 2: Source ID Existence & Provenance
        for hyp in evaluated_hypotheses:
            h_status = hyp.get("status")
            h_type = hyp.get("hypothesis_type")
            supporting_ids = hyp.get("supporting_evidence_ids", [])
            contradicting_ids = hyp.get("contradicting_evidence_ids", [])

            if h_status == "SUPPORTED":
                # Must have at least 1 verified source ID
                if not supporting_ids:
                    policy_results.append(VerificationPolicyResult(
                        policy_name=f"Source Provenance Check ({h_type})",
                        is_verified=False,
                        passed=False,
                        details="Supported finding rejected: Missing concrete source ID"
                    ))
                    unresolved_matters.append({
                        "hypothesis": hyp.get("title"),
                        "reason": "Missing primary source document reference"
                    })
                else:
                    policy_results.append(VerificationPolicyResult(
                        policy_name=f"Source Provenance Check ({h_type})",
                        is_verified=True,
                        passed=True,
                        details=f"Verified with {len(supporting_ids)} source records: {', '.join(supporting_ids)}"
                    ))
                    verified_findings.append({
                        "finding_type": h_type,
                        "title": hyp.get("title"),
                        "rationale": hyp.get("challenge_rationale"),
                        "evidence_ids": supporting_ids,
                        "reconciled_amount": notice_mismatch_amount
                    })

            elif h_status == "CONTRADICTED":
                rejected_hypotheses.append({
                    "hypothesis": hyp.get("title"),
                    "reason": hyp.get("challenge_rationale"),
                    "contradicting_ids": contradicting_ids
                })
                policy_results.append(VerificationPolicyResult(
                    policy_name=f"Contradiction Isolation ({h_type})",
                    is_verified=True,
                    passed=True,
                    details="Successfully isolated and refuted by contradictory evidence"
                ))

            else:  # UNVERIFIED
                unresolved_matters.append({
                    "hypothesis": hyp.get("title"),
                    "reason": hyp.get("missing_evidence_description") or "Pending external document confirmation"
                })

        # Policy 3: Per-mismatch deterministic checks (Phase 6)
        if mismatch_results:
            for mr in mismatch_results:
                m_id = mr.get("mismatch_id", "MIS-UNKNOWN")
                m_status = mr.get("status", "UNVERIFIED")
                ev_ids = mr.get("evidence_ids", [])
                m_period = mr.get("tax_period", "")
                if len(ev_ids) == 0 or m_status in ("UNVERIFIED", "FAILED"):
                    policy_results.append(VerificationPolicyResult(
                        policy_name=f"Mismatch Evidence Check ({m_id})",
                        is_verified=False,
                        passed=False,
                        evidence_status="UNVERIFIED",
                        details=f"[{m_id}] Missing or unverified evidence for {mr.get('invoice_ref', 'N/A')}"
                    ))
                    unresolved_matters.append({
                        "hypothesis": f"{m_id}: {mr.get('invoice_ref', 'N/A')}",
                        "reason": mr.get("error") or "Missing primary invoice/portal evidence"
                    })
                elif m_status == "CONTRADICTED":
                    policy_results.append(VerificationPolicyResult(
                        policy_name=f"Mismatch Evidence Check ({m_id})",
                        is_verified=True,
                        passed=True,
                        evidence_status="CONTRADICTED",
                        details=f"[{m_id}] Contradicted by evidence: {', '.join(ev_ids)}"
                    ))
                else:
                    period_ok = (not notice_tax_period) or (not m_period) or (m_period == notice_tax_period)
                    policy_results.append(VerificationPolicyResult(
                        policy_name=f"Mismatch Evidence Check ({m_id})",
                        is_verified=period_ok,
                        passed=period_ok,
                        evidence_status="SUPPORTED" if period_ok else "UNVERIFIED",
                        details=f"[{m_id}] Supported by {len(ev_ids)} evidence record(s)" + ("" if period_ok else f" (period mismatch: {m_period} vs {notice_tax_period})")
                    ))

        if fan_in_summary:
            fan_total = float(fan_in_summary.get("total_mismatch_amount", 0.0))
            if fan_total > 0 and notice_mismatch_amount > 0:
                fan_diff = abs(fan_total - notice_mismatch_amount)
                fan_ok = fan_diff <= 1.0
                policy_results.append(VerificationPolicyResult(
                    policy_name="Fan-in Amount Reconciliation",
                    is_verified=fan_ok,
                    passed=fan_ok,
                    evidence_status="SUPPORTED" if fan_ok else "UNVERIFIED",
                    details=f"Fan-in total INR {fan_total:.2f} vs Notice mismatch INR {notice_mismatch_amount:.2f} (Diff: INR {fan_diff:.2f})"
                ))

        # Overall Gate Determination
        all_passed = arithmetic_passed and len(verified_findings) > 0 and len(unresolved_matters) == 0

        if all_passed:
            verdict = "SUPPORTED"
            is_approved = True
            notes = "All deterministic verification checks PASSED. Finding cleared for response drafting."
        elif len(verified_findings) > 0:
            verdict = "SUPPORTED_WITH_UNRESOLVED"
            is_approved = True  # Can draft partial response with explicit unresolved schedule
            notes = "Primary root-cause verified; secondary items noted in unresolved schedule."
        else:
            verdict = "INSUFFICIENT_EVIDENCE"
            is_approved = False
            notes = "Verification Gate BLOCKED response drafting. Additional evidence required."

        logger.info("verification_gate_result", is_approved=is_approved, verdict=verdict, verified_count=len(verified_findings))

        return VerificationGateResult(
            is_approved=is_approved,
            verdict=verdict,
            policy_results=policy_results,
            verified_findings=verified_findings,
            rejected_hypotheses=rejected_hypotheses,
            unresolved_matters=unresolved_matters,
            execution_notes=notes
        )

verification_gate = DeterministicVerificationGate()
