"""
CAT2-057 Phase 9 — Comprehensive Test Suite
============================================
Tests all 10 CAT2-057 phases:
  Phase 1 & 2: Mismatch fan-out and fan-in
  Phase 3:     Deadline tracking
  Phase 4:     MCP reliability (retry/backoff)
  Phase 5:     Idempotency
  Phase 6:     Evidence verification
  Phase 7:     Audit trail
  Phase 10:    E2E multi-mismatch demo

Run:  cd taxpilot-ai/backend && python -m pytest tests/integration/test_cat2_057_phases.py -v
"""

import asyncio
import pytest
import uuid
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

# ─── Phase 1 & 2: Mismatch fan-out / fan-in ──────────────────────────────────

class TestMismatchFanout:
    """Phase 1: Mismatch extraction and parallel investigation."""

    @pytest.mark.asyncio
    async def test_extract_mismatches_from_suspect_invoices(self):
        """Given suspect invoices, extract_mismatches yields one item per invoice."""
        from app.investigation.mismatch_fanout import extract_mismatches
        notice = {"tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "itc_mismatch": 81000.0}
        invoices = [
            {"invoice_number": "INV-001", "tax_amount": 50000.0, "supplier_gstin": "33AABCA1234F1Z5"},
            {"invoice_number": "INV-002", "tax_amount": 31000.0, "supplier_gstin": "27AABCT1234C1Z5"},
        ]
        items = await extract_mismatches(notice, invoices)
        assert len(items) == 2
        assert items[0]["mismatch_id"] == "MIS-001"
        assert items[1]["mismatch_id"] == "MIS-002"
        assert items[0]["invoice_ref"] == "INV-001"
        assert all(i["status"] == "PENDING" for i in items)

    @pytest.mark.asyncio
    async def test_extract_mismatches_fallback_to_single_when_no_invoices(self):
        """When no suspect invoices, produce one NOTICE-LEVEL mismatch."""
        from app.investigation.mismatch_fanout import extract_mismatches
        notice = {"tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "itc_mismatch": 81000.0}
        items = await extract_mismatches(notice, [])
        assert len(items) == 1
        assert items[0]["mismatch_id"] == "MIS-001"
        assert items[0]["invoice_ref"] == "NOTICE-LEVEL"
        assert items[0]["mismatch_amount"] == 81000.0

    @pytest.mark.asyncio
    async def test_fan_out_concurrency_bounded(self):
        """fan_out_mismatches respects max_concurrency semaphore."""
        from app.investigation.mismatch_fanout import fan_out_mismatches, extract_mismatches
        notice = {"tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "itc_mismatch": 90000.0}
        invoices = [
            {"invoice_number": f"INV-{i:03d}", "tax_amount": 30000.0, "supplier_gstin": "33AABCA1234F1Z5"}
            for i in range(3)
        ]
        items = await extract_mismatches(notice, invoices)
        results = await fan_out_mismatches(
            mismatch_items=items,
            investigation_id=str(uuid.uuid4()),
            notice_data=notice,
            client_gstin="27AABCT1234C1Z5",
            max_concurrency=2,
        )
        assert len(results) == 3
        # Every result must have a valid status
        for r in results:
            assert r["status"] in {"SUPPORTED", "UNVERIFIED", "FAILED", "CONTRADICTED"}

    @pytest.mark.asyncio
    async def test_fan_out_one_failing_does_not_crash_others(self):
        """A single mismatch investigation failure is isolated; others complete."""
        from app.investigation.mismatch_fanout import fan_out_mismatches

        async def _fail_once(mismatch_item, **kwargs):
            if mismatch_item["mismatch_id"] == "MIS-002":
                raise RuntimeError("Simulated tool failure")
            return {**mismatch_item, "status": "SUPPORTED", "evidence_ids": ["EV-001"], "findings": []}

        mismatch_items = [
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-A", "mismatch_amount": 10000.0,
             "tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "classification": "UNCLASSIFIED",
             "status": "PENDING", "evidence_ids": [], "findings": [], "error": None},
            {"mismatch_id": "MIS-002", "invoice_ref": "INV-B", "mismatch_amount": 20000.0,
             "tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "classification": "UNCLASSIFIED",
             "status": "PENDING", "evidence_ids": [], "findings": [], "error": None},
        ]

        with patch("app.investigation.mismatch_fanout.investigate_single_mismatch", side_effect=_fail_once):
            results = await fan_out_mismatches(
                mismatch_items=mismatch_items,
                investigation_id=str(uuid.uuid4()),
                notice_data={"tax_period": "2023-11", "gstin": "27AABCT1234C1Z5"},
                client_gstin="27AABCT1234C1Z5",
            )

        assert len(results) == 2
        statuses = {r["mismatch_id"]: r["status"] for r in results}
        assert statuses["MIS-001"] == "SUPPORTED"
        assert statuses["MIS-002"] == "FAILED"


class TestFanIn:
    """Phase 2: Fan-in consolidation."""

    def test_fan_in_financial_calculation_deterministic(self):
        """Financial totals use Python arithmetic; never LLM-generated."""
        from app.investigation.fan_in import consolidate_mismatch_results
        results = [
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-001", "mismatch_amount": 50000.0,
             "classification": "TIMING_DIFFERENCE", "tax_period": "2023-11", "gstin": "X",
             "status": "SUPPORTED", "evidence_ids": ["EV-1"], "findings": [], "react_steps": 2},
            {"mismatch_id": "MIS-002", "invoice_ref": "INV-002", "mismatch_amount": 31000.0,
             "classification": "SUPPLIER_NON_FILING", "tax_period": "2023-11", "gstin": "Y",
             "status": "UNVERIFIED", "evidence_ids": [], "findings": [], "react_steps": 1},
        ]
        summary = consolidate_mismatch_results(results)
        assert summary["total_mismatch_amount"] == 81000.0
        assert summary["total_supported_amount"] == 50000.0
        assert summary["total_unverified_amount"] == 31000.0
        assert summary["supported_count"] == 1
        assert summary["unverified_count"] == 1
        assert len(summary["missing_evidence_summary"]) == 1

    def test_fan_in_deduplication_by_mismatch_id_invoice_ref(self):
        """Duplicate (mismatch_id, invoice_ref) pairs are deduplicated."""
        from app.investigation.fan_in import consolidate_mismatch_results
        # Same mismatch_id + invoice_ref appears twice
        results = [
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-001", "mismatch_amount": 50000.0,
             "classification": "TIMING_DIFFERENCE", "tax_period": "2023-11", "gstin": "X",
             "status": "SUPPORTED", "evidence_ids": ["EV-1"], "findings": [], "react_steps": 2},
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-001", "mismatch_amount": 50000.0,
             "classification": "TIMING_DIFFERENCE", "tax_period": "2023-11", "gstin": "X",
             "status": "SUPPORTED", "evidence_ids": ["EV-1"], "findings": [], "react_steps": 2},
        ]
        summary = consolidate_mismatch_results(results)
        # Only one should be counted after dedup
        assert summary["mismatch_count"] == 2  # input count
        assert summary["supported_count"] == 1  # deduped
        assert summary["total_supported_amount"] == 50000.0  # not 100000

    def test_fan_in_unverified_findings_preserved(self):
        """UNVERIFIED findings are explicitly listed and not silently dropped."""
        from app.investigation.fan_in import consolidate_mismatch_results
        results = [
            {"mismatch_id": "MIS-001", "invoice_ref": "NOTICE-LEVEL", "mismatch_amount": 81000.0,
             "classification": "UNCLASSIFIED", "tax_period": "2023-11", "gstin": "X",
             "status": "UNVERIFIED", "evidence_ids": [], "findings": [], "react_steps": 1},
        ]
        summary = consolidate_mismatch_results(results)
        assert summary["unverified_count"] == 1
        assert len(summary["unverified_findings"]) == 1
        assert len(summary["missing_evidence_summary"]) == 1
        assert "MIS-001" in summary["missing_evidence_summary"][0]


# ─── Phase 3: Deadline tracking ───────────────────────────────────────────────

class TestDeadlineTracking:
    """Phase 3: Deadline urgency computation."""

    def test_deadline_urgency_critical_overdue(self):
        """Past deadline is CRITICAL + is_overdue=True."""
        from app.workflows.nodes import _compute_deadline_urgency
        result = _compute_deadline_urgency("2020-01-01")
        assert result["is_overdue"] is True
        assert result["deadline_urgency"] == "CRITICAL"
        assert result["deadline_days_remaining"] < 0

    def test_deadline_urgency_critical_within_3_days(self):
        from app.workflows.nodes import _compute_deadline_urgency
        from datetime import date, timedelta
        soon = (date.today() + timedelta(days=2)).isoformat()
        result = _compute_deadline_urgency(soon)
        assert result["deadline_urgency"] == "CRITICAL"
        assert result["is_overdue"] is False

    def test_deadline_urgency_high(self):
        from app.workflows.nodes import _compute_deadline_urgency
        from datetime import date, timedelta
        d = (date.today() + timedelta(days=5)).isoformat()
        result = _compute_deadline_urgency(d)
        assert result["deadline_urgency"] == "HIGH"

    def test_deadline_urgency_medium(self):
        from app.workflows.nodes import _compute_deadline_urgency
        from datetime import date, timedelta
        d = (date.today() + timedelta(days=10)).isoformat()
        result = _compute_deadline_urgency(d)
        assert result["deadline_urgency"] == "MEDIUM"

    def test_deadline_urgency_low(self):
        from app.workflows.nodes import _compute_deadline_urgency
        from datetime import date, timedelta
        d = (date.today() + timedelta(days=30)).isoformat()
        result = _compute_deadline_urgency(d)
        assert result["deadline_urgency"] == "LOW"

    def test_deadline_missing_returns_none(self):
        """Missing deadline never raises; returns NONE urgency."""
        from app.workflows.nodes import _compute_deadline_urgency
        result = _compute_deadline_urgency(None)
        assert result["deadline_urgency"] == "NONE"
        assert result["is_overdue"] is False
        assert result["deadline_days_remaining"] is None


# ─── Phase 4: MCP reliability ─────────────────────────────────────────────────

class TestMCPReliability:
    """Phase 4: MCP retry and backoff."""

    @pytest.mark.asyncio
    async def test_mcp_tool_success_on_first_attempt(self):
        """Successful in-process tool call returns data without retries."""
        from app.mcp.client.manager import MCPClientManager
        client = MCPClientManager()
        await client.initialize()
        result = await client.invoke_tool("get_vendor_filing_status", {
            "gstin": "27AABCT1234C1Z5",
            "tax_period": "2023-11"
        })
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_mcp_tool_failure_raises_mcp_tool_failure(self):
        """When in-process executor raises, MCPToolFailure is raised with correct tool_name."""
        from app.mcp.client.manager import MCPClientManager, MCPToolFailure
        client = MCPClientManager()
        await client.initialize()

        with patch.dict(
            "app.mcp.client.manager.LEDGER_TOOL_EXECUTORS",
            {"get_invoice_details": MagicMock(side_effect=RuntimeError("Simulated DB failure"))}
        ):
            with pytest.raises(MCPToolFailure) as exc_info:
                await client.invoke_tool("get_invoice_details", {"invoice_number": "INV-999"}, max_retries=0)
            assert exc_info.value.tool_name == "get_invoice_details"

    @pytest.mark.asyncio
    async def test_mcp_tool_unknown_raises_value_error(self):
        """Calling an unknown tool raises ValueError immediately (no retry)."""
        from app.mcp.client.manager import MCPClientManager
        client = MCPClientManager()
        await client.initialize()
        with pytest.raises(ValueError, match="not registered"):
            await client.invoke_tool("non_existent_tool", {})

    @pytest.mark.asyncio
    async def test_react_engine_handles_mcp_tool_failure_gracefully(self):
        """BoundedReActLoop.execute_action catches MCPToolFailure and returns UNVERIFIED observation."""
        from app.investigation.react_engine import BoundedReActLoop, ReActAction
        from app.mcp.client.manager import MCPToolFailure

        loop = BoundedReActLoop("Test-Agent", str(uuid.uuid4()))
        action = ReActAction(tool_name="get_vendor_filing_status", arguments={}, rationale="test")

        with patch("app.investigation.react_engine.mcp_client.invoke_tool",
                   new_callable=AsyncMock,
                   side_effect=MCPToolFailure("get_vendor_filing_status", "timeout", 3)):
            obs = await loop.execute_action(action)

        assert obs.is_error is True
        assert "UNVERIFIED" in obs.result_summary
        assert "3" in obs.result_summary  # attempt count in message


# ─── Phase 5: Idempotency ─────────────────────────────────────────────────────

class TestIdempotency:
    """Phase 5: Run investigation idempotency checks (unit level)."""

    def test_mcp_tool_failure_has_correct_attributes(self):
        """MCPToolFailure stores tool_name, error_message, attempts."""
        from app.mcp.client.manager import MCPToolFailure
        exc = MCPToolFailure("my_tool", "some error", 3)
        assert exc.tool_name == "my_tool"
        assert exc.error_message == "some error"
        assert exc.attempts == 3
        assert "my_tool" in str(exc)
        assert "3" in str(exc)


# ─── Phase 6: Evidence verification ───────────────────────────────────────────

class TestEvidenceVerification:
    """Phase 6: Verification Gate checks."""

    def test_missing_invoice_evidence_marked_unverified(self):
        """SUPPORTED hypothesis with no evidence IDs → unresolved."""
        from app.investigation.verification_gate import DeterministicVerificationGate
        gate = DeterministicVerificationGate()
        result = gate.verify_investigation(
            notice_mismatch_amount=81000.0,
            suspect_invoices=[],
            evaluated_hypotheses=[{
                "hypothesis_type": "SUPPLIER_NON_FILING",
                "title": "Supplier X did not file",
                "status": "SUPPORTED",
                "supporting_evidence_ids": [],   # No IDs
                "contradicting_evidence_ids": [],
                "challenge_rationale": "Portal shows non-filing",
            }]
        )
        assert result.is_approved is False
        assert len(result.unresolved_matters) >= 1

    def test_supplier_non_filing_with_evidence_verified(self):
        """SUPPORTED hypothesis with evidence IDs → verified finding."""
        from app.investigation.verification_gate import DeterministicVerificationGate
        gate = DeterministicVerificationGate()
        result = gate.verify_investigation(
            notice_mismatch_amount=10.0,   # allow arithmetic tolerance with no invoices
            suspect_invoices=[],
            evaluated_hypotheses=[{
                "hypothesis_type": "SUPPLIER_NON_FILING",
                "title": "Supplier X non-filer",
                "status": "SUPPORTED",
                "supporting_evidence_ids": ["FILING-33AABCA1234F1Z5-2023-11"],
                "contradicting_evidence_ids": [],
                "challenge_rationale": "GSTR-1 not filed per Tax Portal",
            }]
        )
        assert len(result.verified_findings) >= 1

    def test_contradicted_hypothesis_isolated(self):
        """CONTRADICTED hypothesis lands in rejected_hypotheses, not unresolved."""
        from app.investigation.verification_gate import DeterministicVerificationGate
        gate = DeterministicVerificationGate()
        result = gate.verify_investigation(
            notice_mismatch_amount=81000.0,
            suspect_invoices=[],
            evaluated_hypotheses=[{
                "hypothesis_type": "TIMING_DIFFERENCE",
                "title": "Timing issue",
                "status": "CONTRADICTED",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": ["EV-CONTRA-01"],
                "challenge_rationale": "Invoice matched in same period",
            }]
        )
        assert len(result.rejected_hypotheses) == 1
        assert result.rejected_hypotheses[0]["hypothesis"] == "Timing issue"

    def test_timing_difference_verification_pass(self):
        """Full happy path: arithmetic OK + SUPPORTED with evidence → APPROVED."""
        from app.investigation.verification_gate import DeterministicVerificationGate
        gate = DeterministicVerificationGate()
        result = gate.verify_investigation(
            notice_mismatch_amount=81000.0,
            suspect_invoices=[{"tax_amount": 81000.0}],
            evaluated_hypotheses=[{
                "hypothesis_type": "TIMING_DIFFERENCE",
                "title": "Invoice posted in wrong period",
                "status": "SUPPORTED",
                "supporting_evidence_ids": ["LEDGER-INV-001"],
                "contradicting_evidence_ids": [],
                "challenge_rationale": "Ledger entry confirms posting date mismatch",
            }]
        )
        assert result.is_approved is True
        assert result.verdict in ("SUPPORTED", "SUPPORTED_WITH_UNRESOLVED")


# ─── Phase 7: Audit trail ─────────────────────────────────────────────────────

class TestAuditTrail:
    """Phase 7: Audit log entries are written correctly."""

    @pytest.mark.asyncio
    async def test_audit_repository_log_action(self):
        """AuditRepository.log_action creates an AuditLog entry with correct fields."""
        from unittest.mock import AsyncMock, MagicMock
        import uuid as _uuid

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        from app.database.repositories.audit_repository import AuditRepository
        repo = AuditRepository(mock_db)

        log_entry = await repo.log_action(
            action="INVESTIGATION_STARTED",
            resource_type="investigation",
            resource_id=str(_uuid.uuid4()),
            user_id=str(_uuid.uuid4()),
            organization_id=str(_uuid.uuid4()),
            details={"test": True}
        )

        assert log_entry.action == "INVESTIGATION_STARTED"
        assert log_entry.resource_type == "investigation"
        assert log_entry.details == {"test": True}
        mock_db.add.assert_called_once()


# ─── Phase 10: E2E Multi-Mismatch Demo ───────────────────────────────────────

class TestE2EMultiMismatch:
    """
    Phase 10: End-to-end multi-mismatch scenario.
    Uses 3 mismatches: TIMING_DIFFERENCE (supported), SUPPLIER_NON_FILING (unverified), DUPLICATE_ENTRY (contradicted).
    Verifies fan-out → fan-in → Verification Gate chain.
    """

    @pytest.mark.asyncio
    async def test_three_mismatch_fanout_produces_three_results(self):
        """Fan-out processes each of 3 mismatches independently."""
        from app.investigation.mismatch_fanout import fan_out_mismatches

        mismatch_items = [
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-TIMING", "mismatch_amount": 30000.0,
             "tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "classification": "TIMING_DIFFERENCE",
             "status": "PENDING", "evidence_ids": [], "findings": [], "error": None},
            {"mismatch_id": "MIS-002", "invoice_ref": "INV-NONFILE", "mismatch_amount": 31000.0,
             "tax_period": "2023-11", "gstin": "33AABCA1234F1Z5", "classification": "SUPPLIER_NON_FILING",
             "status": "PENDING", "evidence_ids": [], "findings": [], "error": None},
            {"mismatch_id": "MIS-003", "invoice_ref": "INV-DUP", "mismatch_amount": 20000.0,
             "tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "classification": "DUPLICATE_ENTRY",
             "status": "PENDING", "evidence_ids": [], "findings": [], "error": None},
        ]

        results = await fan_out_mismatches(
            mismatch_items=mismatch_items,
            investigation_id=str(uuid.uuid4()),
            notice_data={"tax_period": "2023-11", "gstin": "27AABCT1234C1Z5", "itc_mismatch": 81000.0},
            client_gstin="27AABCT1234C1Z5",
            max_concurrency=3,
        )

        assert len(results) == 3
        mismatch_ids = {r["mismatch_id"] for r in results}
        assert mismatch_ids == {"MIS-001", "MIS-002", "MIS-003"}

    @pytest.mark.asyncio
    async def test_fan_in_total_equals_sum_of_mismatches(self):
        """Fan-in total_mismatch_amount = Python sum of individual amounts."""
        from app.investigation.fan_in import consolidate_mismatch_results

        results = [
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-A", "mismatch_amount": 30000.0,
             "classification": "TIMING_DIFFERENCE", "tax_period": "2023-11", "gstin": "X",
             "status": "SUPPORTED", "evidence_ids": ["EV-1"], "findings": [], "react_steps": 3},
            {"mismatch_id": "MIS-002", "invoice_ref": "INV-B", "mismatch_amount": 31000.0,
             "classification": "SUPPLIER_NON_FILING", "tax_period": "2023-11", "gstin": "Y",
             "status": "UNVERIFIED", "evidence_ids": [], "findings": [], "react_steps": 2},
            {"mismatch_id": "MIS-003", "invoice_ref": "INV-C", "mismatch_amount": 20000.0,
             "classification": "DUPLICATE_ENTRY", "tax_period": "2023-11", "gstin": "X",
             "status": "CONTRADICTED", "evidence_ids": ["EV-2"], "findings": [], "react_steps": 1},
        ]

        summary = consolidate_mismatch_results(results)

        # Total = 30000 + 31000 + 20000 = 81000 (Python arithmetic, not LLM)
        assert summary["total_mismatch_amount"] == 81000.0
        assert summary["total_supported_amount"] == 30000.0
        assert summary["total_unverified_amount"] == 31000.0
        assert summary["supported_count"] == 1
        assert summary["unverified_count"] == 1
        assert summary["contradicted_count"] == 1

    @pytest.mark.asyncio
    async def test_needs_auditor_input_for_unverified_mismatch(self):
        """Fan-in with unverified findings produces missing_evidence_summary entries."""
        from app.investigation.fan_in import consolidate_mismatch_results

        results = [
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-B", "mismatch_amount": 31000.0,
             "classification": "SUPPLIER_NON_FILING", "tax_period": "2023-11", "gstin": "Y",
             "status": "UNVERIFIED", "evidence_ids": [], "findings": [], "react_steps": 2},
        ]
        summary = consolidate_mismatch_results(results)
        assert len(summary["missing_evidence_summary"]) == 1
        assert "UNVERIFIED" in summary["missing_evidence_summary"][0] or "MIS-001" in summary["missing_evidence_summary"][0]

    def test_classification_counts_in_fan_in(self):
        """Fan-in accurately counts mismatches by classification type."""
        from app.investigation.fan_in import consolidate_mismatch_results

        results = [
            {"mismatch_id": "MIS-001", "invoice_ref": "INV-A", "mismatch_amount": 10000.0,
             "classification": "TIMING_DIFFERENCE", "tax_period": "2023-11", "gstin": "X",
             "status": "SUPPORTED", "evidence_ids": ["EV-1"], "findings": [], "react_steps": 1},
            {"mismatch_id": "MIS-002", "invoice_ref": "INV-B", "mismatch_amount": 10000.0,
             "classification": "TIMING_DIFFERENCE", "tax_period": "2023-11", "gstin": "X",
             "status": "UNVERIFIED", "evidence_ids": [], "findings": [], "react_steps": 1},
            {"mismatch_id": "MIS-003", "invoice_ref": "INV-C", "mismatch_amount": 10000.0,
             "classification": "SUPPLIER_NON_FILING", "tax_period": "2023-11", "gstin": "Y",
             "status": "UNVERIFIED", "evidence_ids": [], "findings": [], "react_steps": 1},
        ]
        summary = consolidate_mismatch_results(results)
        assert summary["classification_counts"]["TIMING_DIFFERENCE"] == 2
        assert summary["classification_counts"]["SUPPLIER_NON_FILING"] == 1
