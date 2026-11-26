import pytest
import os
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.main import app

SAMPLE_PDF_PATH = os.path.abspath(os.path.join(backend_dir, "..", "sample_documents", "notices", "SYNTHETIC_DRC-01C_demo_notice.pdf"))

@pytest.mark.asyncio
async def test_upload_valid_sample_notice_pdf():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login to obtain token
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@abctraders.demo", "password": "TaxPilot@2024"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Upload actual sample PDF
        assert os.path.exists(SAMPLE_PDF_PATH), f"Sample PDF not found at {SAMPLE_PDF_PATH}"
        with open(SAMPLE_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        files = {"file": ("SYNTHETIC_DRC-01C_demo_notice.pdf", pdf_bytes, "application/pdf")}
        upload_res = await client.post("/api/v1/notices/upload", files=files, headers=headers)
        assert upload_res.status_code == 201

        body = upload_res.json()
        assert body["success"] is True
        data = body["data"]

        # Validate extracted metadata
        assert data["filename"] == "SYNTHETIC_DRC-01C_demo_notice.pdf"
        assert data["file_size_bytes"] == len(pdf_bytes)
        assert data["document_id"] is not None
        assert data["investigation_id"] is not None

        notice = data["notice"]
        assert notice["gstin"] == "34ABCDE1234F1Z5"
        assert notice["notice_type"] == "DRC-01C"
        assert notice["tax_period"] == "2026-05"
        assert notice["itc_claimed"] == 3600.0
        assert notice["itc_available"] == 2160.0
        assert notice["itc_mismatch"] == 1440.0
        assert notice["status"] == "VALIDATED"

@pytest.mark.asyncio
async def test_upload_invalid_file_extension():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@abctraders.demo", "password": "TaxPilot@2024"}
        )
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
        res = await client.post("/api/v1/notices/upload", files=files, headers=headers)
        assert res.status_code == 400
        assert "Unsupported file type" in res.json()["detail"]

@pytest.mark.asyncio
async def test_upload_empty_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@abctraders.demo", "password": "TaxPilot@2024"}
        )
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        files = {"file": ("empty.pdf", b"", "application/pdf")}
        res = await client.post("/api/v1/notices/upload", files=files, headers=headers)
        assert res.status_code == 400
        assert "empty" in res.json()["detail"]

@pytest.mark.asyncio
async def test_upload_unauthenticated_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("notice.pdf", b"%PDF-1.4 mock", "application/pdf")}
        res = await client.post("/api/v1/notices/upload", files=files)
        assert res.status_code == 401
