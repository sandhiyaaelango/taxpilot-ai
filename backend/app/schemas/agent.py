from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    tool_name: str
    mcp_server: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    result_summary: Optional[str] = None
    result_status: str
    duration_ms: Optional[int] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    called_at: Optional[datetime] = None

class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    investigation_id: Any
    agent_name: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    agent_metadata: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    tool_calls: Optional[List[ToolCallResponse]] = []
