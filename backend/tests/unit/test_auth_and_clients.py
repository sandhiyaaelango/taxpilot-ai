import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_login_demo_user():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@abctraders.demo", "password": "TaxPilot@2024"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["user"]["role"] == "ADMIN"

@pytest.mark.asyncio
async def test_get_me():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@abctraders.demo", "password": "TaxPilot@2024"}
        )
        token = login_res.json()["data"]["access_token"]

        # Call /me
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200
        assert me_res.json()["data"]["email"] == "admin@abctraders.demo"

@pytest.mark.asyncio
async def test_list_clients():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@abctraders.demo", "password": "TaxPilot@2024"}
        )
        token = login_res.json()["data"]["access_token"]

        clients_res = await client.get(
            "/api/v1/clients",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert clients_res.status_code == 200
        data = clients_res.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert any(c["business_name"] == "ABC Traders Pvt Ltd" for c in data["data"])
