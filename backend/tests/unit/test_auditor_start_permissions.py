import os
import sys
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import update

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.main import app
from app.database.session import AsyncSessionLocal
from app.database.models.investigation import Investigation
from app.database.models.organization import Organization
from app.database.models.user import User
from app.config.security import hash_password, decode_access_token

SAMPLE_PDF_PATH = os.path.abspath(
    os.path.join(backend_dir, "..", "sample_documents", "notices", "SYNTHETIC_DRC-01C_demo_notice.pdf")
)


async def _login(client: AsyncClient, email: str, password: str = "TaxPilot@2024"):
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["data"]


@pytest.mark.asyncio
async def test_role_consistency_jwt_and_me_endpoint():
    """Verify two-role consistency: no REVIEWER or OWNER returned in login/JWT/me."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Auditor (former reviewer@abctraders.demo)
        auditor_login = await _login(client, "reviewer@abctraders.demo")
        assert auditor_login["user"]["role"] == "AUDITOR"
        jwt_claims = decode_access_token(auditor_login["access_token"])
        assert jwt_claims["role"] == "AUDITOR"

        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auditor_login['access_token']}"}
        )
        assert me_res.status_code == 200
        assert me_res.json()["data"]["role"] == "AUDITOR"

        # 2. Admin (admin@abctraders.demo)
        admin_login = await _login(client, "admin@abctraders.demo")
        assert admin_login["user"]["role"] == "ADMIN"
        admin_claims = decode_access_token(admin_login["access_token"])
        assert admin_claims["role"] == "ADMIN"

        admin_me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_login['access_token']}"}
        )
        assert admin_me.status_code == 200
        assert admin_me.json()["data"]["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_auditor_upload_and_start_investigation_workflow():
    """
    Covers:
    - Auditor can upload a notice
    - Auditor can start an authorized investigation
    - Reviewer role is not required anywhere
    - Successful start triggers the actual workflow
    - Repeated start requests on completed/AWAITING_APPROVAL investigation are rejected safely
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_data = await _login(client, "reviewer@abctraders.demo")
        headers = {"Authorization": f"Bearer {login_data['access_token']}"}

        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        upload_res = await client.post(
            "/api/v1/notices/upload",
            files={"file": ("SYNTHETIC_DRC-01C_demo_notice.pdf", pdf_bytes, "application/pdf")},
            headers=headers
        )
        assert upload_res.status_code == 201, upload_res.text
        inv_id = upload_res.json()["data"]["investigation_id"]

        run_res = await client.post(f"/api/v1/investigations/{inv_id}/run", headers=headers)
        assert run_res.status_code == 200, f"Auditor start failed: {run_res.text}"
        run_data = run_res.json()["data"]
        assert run_data["status"] == "AWAITING_APPROVAL"
        assert run_data["hypotheses_count"] > 0

        # Repeated start request after workflow completed to AWAITING_APPROVAL
        repeat_res = await client.post(f"/api/v1/investigations/{inv_id}/run", headers=headers)
        assert repeat_res.status_code == 400
        assert "Cannot start AI investigation" in repeat_res.json()["detail"]


@pytest.mark.asyncio
async def test_unauthenticated_cannot_start_investigation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(f"/api/v1/investigations/{uuid.uuid4()}/run")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_cannot_approve_or_start_auditor_investigation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auditor_data = await _login(client, "ca@abctraders.demo")
        auditor_headers = {"Authorization": f"Bearer {auditor_data['access_token']}"}

        admin_data = await _login(client, "admin@abctraders.demo")
        admin_headers = {"Authorization": f"Bearer {admin_data['access_token']}"}

        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        upload_res = await client.post(
            "/api/v1/notices/upload",
            files={"file": ("SYNTHETIC_DRC-01C_demo_notice.pdf", pdf_bytes, "application/pdf")},
            headers=auditor_headers
        )
        assert upload_res.status_code == 201
        inv_id = upload_res.json()["data"]["investigation_id"]

        # Admin cannot start Auditor investigation
        admin_run = await client.post(f"/api/v1/investigations/{inv_id}/run", headers=admin_headers)
        assert admin_run.status_code == 403

        # Admin cannot approve Auditor investigation
        admin_approve = await client.post(
            f"/api/v1/approvals/{inv_id}",
            json={"action": "APPROVE", "notes": "Unauthorized admin attempt"},
            headers=admin_headers
        )
        assert admin_approve.status_code == 403


@pytest.mark.asyncio
async def test_cross_organization_isolation_on_start():
    """Auditor from Org B cannot start Org A's investigation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Org A auditor uploads notice
        org_a_login = await _login(client, "ca@abctraders.demo")
        org_a_headers = {"Authorization": f"Bearer {org_a_login['access_token']}"}

        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        upload_res = await client.post(
            "/api/v1/notices/upload",
            files={"file": ("SYNTHETIC_DRC-01C_demo_notice.pdf", pdf_bytes, "application/pdf")},
            headers=org_a_headers
        )
        assert upload_res.status_code == 201
        inv_id = upload_res.json()["data"]["investigation_id"]

        # Register Org B Auditor
        unique_email = f"orgb_auditor_{uuid.uuid4().hex[:6]}@otherfirm.demo"
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "StrongPassword@123",
                "full_name": "Org B Auditor",
                "organization_name": "Other Firm LLP",
                "role": "AUDITOR"
            }
        )
        assert reg_res.status_code == 200
        org_b_headers = {"Authorization": f"Bearer {reg_res.json()['data']['access_token']}"}

        # Org B Auditor tries to start Org A's investigation
        cross_res = await client.post(f"/api/v1/investigations/{inv_id}/run", headers=org_b_headers)
        assert cross_res.status_code == 404


@pytest.mark.asyncio
async def test_invalid_and_in_progress_status_rejected():
    """Rejects 409 for already-running INVESTIGATING and 400 for APPROVED."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auditor_login = await _login(client, "ca@abctraders.demo")
        headers = {"Authorization": f"Bearer {auditor_login['access_token']}"}

        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        upload_res = await client.post(
            "/api/v1/notices/upload",
            files={"file": ("SYNTHETIC_DRC-01C_demo_notice.pdf", pdf_bytes, "application/pdf")},
            headers=headers
        )
        inv_id = upload_res.json()["data"]["investigation_id"]

        # Simulate active INVESTIGATING state -> 409 Conflict
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Investigation)
                .where(Investigation.id == uuid.UUID(inv_id))
                .values(status="INVESTIGATING")
            )
            await db.commit()

        conflict_res = await client.post(f"/api/v1/investigations/{inv_id}/run", headers=headers)
        assert conflict_res.status_code == 409

        # Simulate APPROVED state -> 400 Bad Request
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Investigation)
                .where(Investigation.id == uuid.UUID(inv_id))
                .values(status="APPROVED")
            )
            await db.commit()

        invalid_res = await client.post(f"/api/v1/investigations/{inv_id}/run", headers=headers)
        assert invalid_res.status_code == 400
