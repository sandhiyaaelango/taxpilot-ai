import pytest
import os
import sys
import json
import uuid
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.main import app
from app.database.session import AsyncSessionLocal
from app.database.models.agent import AgentRun, ToolCall
from app.database.models.evidence import Hypothesis, EvidenceRecord
from app.database.models.approval import Report, Approval
from app.database.models.investigation import Investigation
from app.investigation.stream_manager import stream_manager
from app.config.logging import get_logger

logger = get_logger("test_e2e_investigation_stream")

SAMPLE_PDF_PATH = os.path.abspath(
    os.path.join(backend_dir, "..", "sample_documents", "notices", "SYNTHETIC_DRC-01C_demo_notice.pdf")
)

STEP_TIMEOUT_SECONDS = 15.0

@pytest.mark.asyncio
async def test_end_to_end_notice_upload_to_investigation_and_approval():
    """
    Complete End-to-End Workflow & Telemetry Integration Test:
    1. Authenticate as Chartered Accountant
    2. Upload synthetic DRC-01C PDF notice
    3. Trigger multi-agent investigation workflow
    4. Verify live SSE stream events & telemetry buffer (with bounded timeout & streaming reader)
    5. Verify database persistence (AgentRuns, ToolCalls, Hypotheses, Evidence, Reports)
    6. Submit accountant review & approval
    7. Verify status progression from AWAITING_APPROVAL -> APPROVED and report marked FINAL
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Login
        logger.info("[E2E TEST] Step 1: Logging in as Auditor (Chartered Accountant)...")
        login_res = await asyncio.wait_for(
            client.post(
                "/api/v1/auth/login",
                json={"email": "ca@abctraders.demo", "password": "TaxPilot@2024"}
            ),
            timeout=STEP_TIMEOUT_SECONDS
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("[E2E TEST] Step 1 SUCCESS: Authenticated successfully")

        # Step 2: Upload Notice PDF
        logger.info("[E2E TEST] Step 2: Uploading notice PDF...")
        assert os.path.exists(SAMPLE_PDF_PATH), f"Notice PDF missing: {SAMPLE_PDF_PATH}"
        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        upload_res = await asyncio.wait_for(
            client.post(
                "/api/v1/notices/upload",
                files={"file": ("SYNTHETIC_DRC-01C_demo_notice.pdf", pdf_bytes, "application/pdf")},
                headers=headers
            ),
            timeout=STEP_TIMEOUT_SECONDS
        )
        assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
        upload_data = upload_res.json()["data"]
        inv_id = upload_data["investigation_id"]
        assert inv_id is not None
        logger.info(f"[E2E TEST] Step 2 SUCCESS: Notice uploaded, investigation_id={inv_id}")

        # Step 3: Run Multi-Agent Investigation Workflow
        logger.info("[E2E TEST] Step 3: Executing multi-agent workflow...")
        run_res = await asyncio.wait_for(
            client.post(f"/api/v1/investigations/{inv_id}/run", headers=headers),
            timeout=STEP_TIMEOUT_SECONDS
        )
        assert run_res.status_code == 200, f"Run failed: {run_res.text}"
        run_body = run_res.json()["data"]
        assert run_body["status"] == "AWAITING_APPROVAL"
        assert run_body["approval_required"] is True
        assert run_body["hypotheses_count"] > 0
        logger.info("[E2E TEST] Step 3 SUCCESS: Workflow executed, status=AWAITING_APPROVAL")

        # Step 4: Verify Live SSE Event Streaming
        logger.info("[E2E TEST] Step 4: Verifying SSE telemetry stream...")
        # 4a. Verify buffered history contains required lifecycle telemetry events
        history = stream_manager.get_history(inv_id)
        assert len(history) > 0, "No SSE events recorded in stream_manager history"

        event_types = [e["event"] for e in history]
        assert "node_transition" in event_types, "Missing node_transition event"
        assert "agent_started" in event_types, "Missing agent_started event"
        assert "agent_completed" in event_types, "Missing agent_completed event"
        assert "tool_call_started" in event_types, "Missing tool_call_started event"
        assert "tool_call_completed" in event_types, "Missing tool_call_completed event"
        assert "verification_gate_evaluated" in event_types, "Missing verification_gate_evaluated event"

        # 4b. Verify actual SSE stream endpoint via streaming context manager (bounded, non-blocking)
        received_lines = []
        async with client.stream("GET", f"/api/v1/investigations/{inv_id}/stream") as stream_res:
            assert stream_res.status_code == 200
            async for line in stream_res.aiter_lines():
                if line.strip():
                    received_lines.append(line.strip())
                if len(received_lines) >= 3:
                    break
        assert any("data:" in l for l in received_lines), "Expected data: lines in SSE stream"

        # 4c. Verify replay_only endpoint closes cleanly with full history
        replay_res = await asyncio.wait_for(
            client.get(f"/api/v1/investigations/{inv_id}/stream?replay_only=true"),
            timeout=STEP_TIMEOUT_SECONDS
        )
        assert replay_res.status_code == 200
        assert "data:" in replay_res.text
        logger.info("[E2E TEST] Step 4 SUCCESS: SSE stream verified without blocking")

        # Step 5: Verify Database Persistence
        logger.info("[E2E TEST] Step 5: Verifying DB persistence...")
        inv_uuid = uuid.UUID(inv_id)
        async with AsyncSessionLocal() as session:
            # 5a. Check Agent Runs
            runs_query = await session.execute(
                select(AgentRun).where(AgentRun.investigation_id == inv_uuid)
            )
            agent_runs = runs_query.scalars().all()
            assert len(agent_runs) >= 4, f"Expected at least 4 AgentRuns, got {len(agent_runs)}"
            run_agents = {r.agent_name for r in agent_runs}
            assert "Notice Parser Agent" in run_agents
            assert "Ledger Matcher Agent" in run_agents
            assert "Root-Cause Investigator" in run_agents
            assert "Evidence Challenge Engine" in run_agents
            assert "Verification Gate" in run_agents
            assert "Response Drafter Agent" in run_agents

            # 5b. Check Tool Calls
            tool_calls_query = await session.execute(
                select(ToolCall).join(AgentRun).where(AgentRun.investigation_id == inv_uuid)
            )
            tool_calls = tool_calls_query.scalars().all()
            assert len(tool_calls) > 0, "Expected persistent ToolCall records"
            for tc in tool_calls:
                assert tc.tool_name is not None
                assert tc.result_status in ["SUCCESS", "ERROR"]
                assert tc.duration_ms >= 0

            # 5c. Check Hypotheses
            hyps_query = await session.execute(
                select(Hypothesis).where(Hypothesis.investigation_id == inv_uuid)
            )
            hyps = hyps_query.scalars().all()
            assert len(hyps) > 0, "Expected persisted Hypothesis records"
            for h in hyps:
                assert h.status in ["SUPPORTED", "CONTRADICTED", "UNVERIFIED"]
                assert h.confidence_score is not None

            # 5d. Check Draft Report
            rep_query = await session.execute(
                select(Report).where(Report.investigation_id == inv_uuid)
            )
            reports = rep_query.scalars().all()
            assert len(reports) > 0, "Expected Draft Report to be saved"
            draft_report = next((r for r in reports if r.report_type == "RESPONSE_DRAFT"), None)
            assert draft_report is not None
            assert draft_report.content is not None
            assert len(str(draft_report.content)) > 100
        logger.info("[E2E TEST] Step 5 SUCCESS: All database records persisted and verified")

        # Step 6: Submit Chartered Accountant Review & Approval
        logger.info("[E2E TEST] Step 6: Submitting CA approval...")
        approval_payload = {
            "action": "APPROVE",
            "notes": "Verified Section 16(2) compliance and matching invoices. Ready for submission.",
            "edited_content": None
        }
        app_res = await asyncio.wait_for(
            client.post(
                f"/api/v1/approvals/{inv_id}",
                json=approval_payload,
                headers=headers
            ),
            timeout=STEP_TIMEOUT_SECONDS
        )
        assert app_res.status_code == 200, f"Approval submission failed: {app_res.text}"
        app_data = app_res.json()["data"]
        assert app_data["action"] == "APPROVE"
        assert app_data["is_final"] is True
        logger.info("[E2E TEST] Step 6 SUCCESS: Approval submitted")

        # Step 7: Verify Investigation is now APPROVED and Report marked FINAL
        logger.info("[E2E TEST] Step 7: Verifying status APPROVED and Report FINAL...")
        inv_check = await asyncio.wait_for(
            client.get(f"/api/v1/investigations/{inv_id}", headers=headers),
            timeout=STEP_TIMEOUT_SECONDS
        )
        assert inv_check.status_code == 200
        inv_status = inv_check.json()["data"]["status"]
        assert inv_status == "APPROVED"

        async with AsyncSessionLocal() as session:
            final_rep_query = await session.execute(
                select(Report).where(Report.investigation_id == inv_uuid, Report.report_type == "FINAL")
            )
            final_report = final_rep_query.scalar_one_or_none()
            assert final_report is not None, "Draft report was not promoted to FINAL on approval"
        logger.info("[E2E TEST] Step 7 SUCCESS: Final status is APPROVED and report is FINAL")
