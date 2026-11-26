from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, clients, investigations, notices,
    evidence, approvals, reports, agents, jobs, audit, analytics
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(investigations.router, prefix="/investigations", tags=["Investigations"])
api_router.include_router(notices.router, prefix="/notices", tags=["Notices"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(agents.router, prefix="/mcp", tags=["MCP"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
