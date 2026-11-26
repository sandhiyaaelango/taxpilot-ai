import pytest
import os
import sys
import uuid
from httpx import AsyncClient, ASGITransport

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.main import app

SAMPLE_PDF_PATH = os.path.join(
    backend_dir, "uploads", "notices", "f1a6291e050f4530b4650e460a6a616c_sample_gst_mismatch_notice_for_taxpilot.pdf"
)

@pytest.mark.asyncio
async def test_full_persistence_draft_approval_history_and_pdf_export():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login as Auditor
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "ca@abctraders.demo", "password": "TaxPilot@2024"}
        )
        assert login_res.status_code == 200
        auditor_token = login_res.json()["data"]["access_token"]
        auditor_headers = {"Authorization": f"Bearer {auditor_token}"}

        # Login as Admin for negative role test
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@abctraders.demo", "password": "TaxPilot@2024"}
        )
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

        # 2. Upload valid GST notice
        assert os.path.exists(SAMPLE_PDF_PATH)
        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        up_res = await client.post(
            "/api/v1/notices/upload",
            files={"file": ("sample_gst_mismatch_notice_for_taxpilot.pdf", pdf_bytes, "application/pdf")},
            headers=auditor_headers
        )
        assert up_res.status_code == 201
        inv_id = up_res.json()["data"]["investigation_id"]

        # 3. Start AI Investigation
        run_res = await client.post(f"/api/v1/investigations/{inv_id}/run", headers=auditor_headers)
        assert run_res.status_code == 200
        assert run_res.json()["data"]["status"] == "AWAITING_APPROVAL"

        # 4. Verify Investigation appears in History (GET /investigations)
        hist_res = await client.get("/api/v1/investigations?page_size=50", headers=auditor_headers)
        assert hist_res.status_code == 200
        hist_ids = [item["id"] for item in hist_res.json()["data"]]
        assert inv_id in hist_ids, "Investigation missing from Investigation History"

        # 5. Verify draft exists in GET /reports/{inv_id}
        rep_res = await client.get(f"/api/v1/reports/{inv_id}", headers=auditor_headers)
        assert rep_res.status_code == 200
        rep_data = rep_res.json()["data"]
        assert rep_data["report_type"] == "RESPONSE_DRAFT"
        assert rep_data["content"]["executive_summary"]

        # 6. Edit and save draft
        edited_summary = "AUDITOR EDITED: Verified ITC of INR 1,40,000.00 against supplier GSTR-1 in subsequent period."
        edit_res = await client.post(
            f"/api/v1/approvals/{inv_id}",
            json={
                "action": "EDIT",
                "notes": "Updated executive summary",
                "edited_content": {
                    "title": "EDITED REPLY TO DRC-01A",
                    "executive_summary": edited_summary
                }
            },
            headers=auditor_headers
        )
        assert edit_res.status_code == 200

        # 7. Re-fetch draft and verify edit persisted
        rep_res2 = await client.get(f"/api/v1/reports/{inv_id}", headers=auditor_headers)
        assert rep_res2.status_code == 200
        assert rep_res2.json()["data"]["content"]["executive_summary"] == edited_summary
        assert rep_res2.json()["data"]["title"] == "EDITED REPLY TO DRC-01A"

        # 8. Negative test: PDF download BEFORE approval must be rejected (400)
        pre_pdf = await client.get(f"/api/v1/reports/{inv_id}/download", headers=auditor_headers)
        assert pre_pdf.status_code == 400

        # 9. Negative test: Admin cannot approve investigation (403)
        admin_app = await client.post(
            f"/api/v1/approvals/{inv_id}",
            json={"action": "APPROVE", "notes": "Admin attempt"},
            headers=admin_headers
        )
        assert admin_app.status_code == 403

        # 10. Auditor approves and finalizes
        app_res = await client.post(
            f"/api/v1/approvals/{inv_id}",
            json={"action": "APPROVE", "notes": "Final Auditor sign-off verified."},
            headers=auditor_headers
        )
        assert app_res.status_code == 200
        assert app_res.json()["data"]["is_final"] is True

        # 11. Duplicate approval attempt rejected (409)
        dup_res = await client.post(
            f"/api/v1/approvals/{inv_id}",
            json={"action": "APPROVE", "notes": "Duplicate attempt"},
            headers=auditor_headers
        )
        assert dup_res.status_code == 409

        # 12. Verify status is APPROVED in History & Approved Reports query
        app_list = await client.get("/api/v1/investigations?status=APPROVED&page_size=50", headers=auditor_headers)
        assert app_list.status_code == 200
        assert inv_id in [i["id"] for i in app_list.json()["data"]]

        # 13. Download PDF twice and verify valid PDF & deterministic persistence
        pdf_res1 = await client.get(f"/api/v1/reports/{inv_id}/download", headers=auditor_headers)
        assert pdf_res1.status_code == 200
        assert pdf_res1.headers["content-type"] == "application/pdf"
        assert pdf_res1.content.startswith(b"%PDF-")
        assert len(pdf_res1.content) > 1000

        pdf_res2 = await client.get(f"/api/v1/reports/{inv_id}/download", headers=auditor_headers)
        assert pdf_res2.status_code == 200
        assert pdf_res2.content == pdf_res1.content

        # 14. Negative tests: invalid ID & unauthorized
        bad_id = str(uuid.uuid4())
        assert (await client.get(f"/api/v1/investigations/{bad_id}", headers=auditor_headers)).status_code == 404
        assert (await client.get(f"/api/v1/reports/{bad_id}", headers=auditor_headers)).status_code == 404
        assert (await client.get(f"/api/v1/reports/{inv_id}/download")).status_code == 401
