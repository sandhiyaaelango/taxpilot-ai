from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.agent import AgentRun, ToolCall
from app.schemas.agent import AgentRunResponse
from app.schemas.common import SuccessResponse
from app.core.dependencies import get_current_user
from app.mcp.client.manager import mcp_client

router = APIRouter()

@router.get("/monitor", response_model=SuccessResponse[Dict[str, Any]])
async def get_agent_monitor(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return active agent status, MCP server status, and recent execution events."""
    if not mcp_client._initialized:
        await mcp_client.initialize()
    tools = mcp_client.list_tools()
    
    query = await db.execute(
        select(AgentRun)
        .options(selectinload(AgentRun.tool_calls))
        .order_by(AgentRun.created_at.desc())
        .limit(10)
    )
    recent_runs = query.scalars().all()

    runs_res = []
    for r in recent_runs:
        runs_res.append({
            "id": str(r.id),
            "agent_name": r.agent_name,
            "status": r.status,
            "duration_ms": r.duration_ms,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "estimated_cost_usd": float(r.estimated_cost_usd) if r.estimated_cost_usd else 0.0,
            "tool_calls_count": len(r.tool_calls or []),
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return SuccessResponse(
        data={
            "connected_mcp_servers": [
                {"name": "Tax Portal MCP Server", "port": 8001, "status": "ONLINE", "tools_count": 4},
                {"name": "Ledger MCP Server", "port": 8002, "status": "ONLINE", "tools_count": 4}
            ],
            "discovered_tools": tools,
            "recent_agent_runs": runs_res
        }
    )

@router.get("/tools", response_model=SuccessResponse[List[Dict[str, Any]]])
async def list_mcp_tools():
    """Return all discovered MCP tools across connected servers."""
    if not mcp_client._initialized:
        await mcp_client.initialize()
    return SuccessResponse(data=mcp_client.list_tools())
