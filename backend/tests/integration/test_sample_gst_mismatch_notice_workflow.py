import pytest
import os
import sys
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

logger = get_logger("test_sample_gst_mismatch_workflow")

SAMPLE_PDF_PATH = os.path.join(
    backend_dir, "uploads", "notices", "f1a6291e050f4530b4650e460a6a616c_sample_gst_mismatch_notice_for_taxpilot.pdf"
)

STEP_TIMEOUT_SECONDS = 30.0

@pytest.mark.asyncio
async def test_sample_notice_full_investigation_and_approval():
    """
    Complete end-to-end test with the user's uploaded synthetic notice:
    1. Authenticate as Auditor
    2. Upload sample_gst_mismatch_notice_for_taxpilot.pdf
    3. Run AI Investigation
    4. Verify all 6 stages execute:
       - Supervisor Agent
       - Notice Parser Agent
       - Ledger Matcher Agent
       - Root-Cause Investigator
       - Evidence Challenge Engine
       - Verification Gate
       - Response Drafter Agent
    5. Verify GET /api/v1/investigations/{id} returns agent_runs
    6. Verify Investigation status transitions to AWAITING_APPROVAL
    7. Verify Draft Report is generated
    8. Verify Auditor review & approval transitions status to APPROVED
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Login as Auditor
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "ca@abctraders.demo", "password": "TaxPilot@2024"}
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Upload Notice PDF
        assert os.path.exists(SAMPLE_PDF_PATH), f"Notice PDF missing: {SAMPLE_PDF_PATH}"
        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        upload_res = await client.post(
            "/api/v1/notices/upload",
            files={"file": ("sample_gst_mismatch_notice_for_taxpilot.pdf", pdf_bytes, "application/pdf")},
            headers=headers
        )
        assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
        inv_id = upload_res.json()["data"]["investigation_id"]
        assert inv_id is not None

        # Step 3: Run AI Investigation
        run_res = await client.post(
            f"/api/v1/investigations/{inv_id}/run",
            headers=headers
        )
        assert run_res.status_code == 200, f"Run failed: {run_res.text}"
        run_data = run_res.json()["data"]
        assert run_data["status"] == "AWAITING_APPROVAL"

        # Step 4: Verify GET /api/v1/investigations/{id} returns all agent runs
        get_res = await client.get(
            f"/api/v1/investigations/{inv_id}",
            headers=headers
        )
        assert get_res.status_code == 200
        inv_detail = get_res.json()["data"]
        assert inv_detail["status"] == "AWAITING_APPROVAL"
        
        runs = inv_detail.get("agent_runs", [])
        assert len(runs) >= 6, f"Expected at least 6 agent runs, got {len(runs)}"
        
        agent_names = {r["agent_name"] for r in runs}
        assert "Supervisor Agent" in agent_names
        assert "Notice Parser Agent" in agent_names
        assert "Ledger Matcher Agent" in agent_names
        assert "Root-Cause Investigator" in agent_names
        assert "Evidence Challenge Engine" in agent_names
        assert "Verification Gate" in agent_names
        assert "Response Drafter Agent" in agent_names

        # Verify all executed successfully
        for r in runs:
            assert r["status"] in ["COMPLETED", "SKIPPED"], f"Agent {r['agent_name']} has status {r['status']}"
            assert r["duration_ms"] is not None
            assert r["duration_ms"] >= 0

        # Step 5: Verify Report was generated
        async with AsyncSessionLocal() as session:
            inv_uuid = uuid.UUID(inv_id)
            rep_query = await session.execute(
                select(Report).where(Report.investigation_id == inv_uuid)
            )
            reports = rep_query.scalars().all()
            assert len(reports) > 0, "No reports generated"
            draft_rep = next((r for r in reports if r.report_type == "RESPONSE_DRAFT"), None)
            assert draft_rep is not None
            assert draft_rep.content is not None

        # Step 6: Verify Auditor review and approval
        approval_res = await client.post(
            f"/api/v1/approvals/{inv_id}",
            json={
                "action": "APPROVE",
                "notes": "Verified Section 16(2) grounds and timing difference evidence.",
                "edited_content": None
            },
            headers=headers
        )
        assert approval_res.status_code == 200, f"Approval failed: {approval_res.text}"
        assert approval_res.json()["data"]["action"] == "APPROVE"
        assert approval_res.json()["data"]["is_final"] is True

        # Step 7: Verify status is now APPROVED
        final_check = await client.get(
            f"/api/v1/investigations/{inv_id}",
            headers=headers
        )
        assert final_check.status_code == 200
        assert final_check.json()["data"]["status"] == "APPROVED"
