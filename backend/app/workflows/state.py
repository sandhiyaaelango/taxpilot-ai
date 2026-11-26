from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class InvestigationWorkflowState(TypedDict, total=False):
    # Core identifiers
    investigation_id: str
    organization_id: str
    client_id: str
    client_name: str
    client_gstin: str
    
    # Document / Notice data
    notice_text: str
    notice_data: Dict[str, Any]
    notice_valid: bool
    notice_validation_errors: List[str]

    # Planning
    investigation_plan: Dict[str, Any]
    invoice_tasks: List[Dict[str, Any]]

    # --- Phase 1: Mismatch-level fan-out ---
    # Each item: {mismatch_id, invoice_ref, mismatch_amount, tax_period, gstin,
    #             classification, status, evidence_ids, findings, error}
    mismatch_items: List[Dict[str, Any]]

    # --- Phase 2: Fan-in consolidated results ---
    # Each item: same structure as mismatch_items + status after investigation
    mismatch_results: List[Dict[str, Any]]
    # Consolidated summary from fan_in.consolidate_mismatch_results()
    fan_in_summary: Dict[str, Any]

    # --- Phase 3: Deadline tracking ---
    response_deadline: Optional[str]      # ISO date string YYYY-MM-DD from notice
    deadline_days_remaining: Optional[int]  # Computed at workflow start
    is_overdue: Optional[bool]
    deadline_urgency: Optional[str]       # CRITICAL|HIGH|MEDIUM|LOW|NONE

    # Investigation findings
    suspect_invoices: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    evidence_records: List[Dict[str, Any]]
    
    # Challenge and Verification
    evaluated_hypotheses: List[Dict[str, Any]]
    verification_passed: bool
    verification_verdict: str  # SUPPORTED / CONTRADICTED / INSUFFICIENT_EVIDENCE
    verification_details: Dict[str, Any]

    # Drafting & Approval
    response_draft: Optional[Dict[str, Any]]
    approval_required: bool
    approval_status: str  # PENDING / APPROVED / REJECTED / NEEDS_MORE_EVIDENCE
    approval_notes: Optional[str]
    reviewer_id: Optional[str]

    # --- Phase 5: Idempotency ---
    run_idempotency_key: Optional[str]    # Header Idempotency-Key from /run endpoint

    # Execution telemetry
    current_node: str
    step_history: List[str]
    error: Optional[str]
    checkpoint_id: Optional[str]
    is_completed: bool
    reinvestigation_count: int            # Number of reinvestigation cycles
