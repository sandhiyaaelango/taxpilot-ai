import time
from typing import Dict, Any, List, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
from app.mcp.client.manager import mcp_client, MCPToolFailure
from app.config.logging import get_logger
from app.investigation.stream_manager import stream_manager

logger = get_logger("react_engine")

class ReActAction(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    rationale: str

class ReActObservation(BaseModel):
    result_summary: str
    data: Dict[str, Any]
    is_error: bool = False
    duration_ms: int = 0

class ReActStep(BaseModel):
    iteration: int
    rationale: str
    action: ReActAction
    observation: ReActObservation

class ReActExecutionLog(BaseModel):
    agent_name: str
    investigation_id: str
    total_iterations: int
    tool_calls_count: int
    token_usage_estimated: int
    steps: List[ReActStep] = []
    final_verdict: str
    final_data: Dict[str, Any] = {}

class BoundedReActLoop:
    """
    Enterprise ReAct Investigation Loop Engine.
    Executes OBSERVE → REASON → ACT → OBSERVE RESULT → UPDATE STATE → EVALUATE.
    Enforces maximum iterations (default 8), tool call budgets, and structured logging.
    """
    def __init__(
        self,
        agent_name: str,
        investigation_id: str,
        max_iterations: int = 8,
        tool_call_budget: int = 12
    ):
        self.agent_name = agent_name
        self.investigation_id = investigation_id
        self.max_iterations = max_iterations
        self.tool_call_budget = tool_call_budget
        self.steps: List[ReActStep] = []
        self.tool_calls_made = 0

    async def execute_action(self, action: ReActAction) -> ReActObservation:
        """Call MCP tool and record duration, outcome, and provenance."""
        mcp_server = "Ledger MCP Server" if any(k in action.tool_name.lower() for k in ["invoice", "ledger", "entries"]) else "Tax Portal MCP Server"

        # Emit live tool call start event
        try:
            await stream_manager.broadcast(self.investigation_id, "tool_call_started", {
                "agent_name": self.agent_name,
                "tool_name": action.tool_name,
                "mcp_server": mcp_server,
                "arguments": action.arguments,
                "rationale": action.rationale
            })
        except Exception:
            pass

        if self.tool_calls_made >= self.tool_call_budget:
            obs = ReActObservation(
                result_summary="Tool call budget exceeded",
                data={"error": "BUDGET_EXCEEDED"},
                is_error=True
            )
            try:
                await stream_manager.broadcast(self.investigation_id, "tool_call_completed", {
                    "agent_name": self.agent_name,
                    "tool_name": action.tool_name,
                    "mcp_server": mcp_server,
                    "arguments": action.arguments,
                    "result_status": "ERROR",
                    "duration_ms": 0,
                    "result_summary": "Tool call budget exceeded",
                    "retry_count": 0
                })
            except Exception:
                pass
            return obs

        self.tool_calls_made += 1
        start_time = time.time()
        try:
            res_data = await mcp_client.invoke_tool(action.tool_name, action.arguments)
            duration_ms = int((time.time() - start_time) * 1000)
            summary = f"Tool '{action.tool_name}' returned {len(res_data)} fields successfully."
            if "source_id" in res_data:
                summary += f" Source ID: {res_data['source_id']}."

            obs = ReActObservation(
                result_summary=summary,
                data=res_data,
                is_error=False,
                duration_ms=duration_ms
            )

            try:
                await stream_manager.broadcast(self.investigation_id, "tool_call_completed", {
                    "agent_name": self.agent_name,
                    "tool_name": action.tool_name,
                    "mcp_server": mcp_server,
                    "arguments": action.arguments,
                    "result_status": "SUCCESS",
                    "duration_ms": duration_ms,
                    "result_summary": summary,
                    "retry_count": 0
                })
            except Exception:
                pass

            return obs
        except MCPToolFailure as mcp_err:
            # Phase 4: MCPToolFailure = exhausted retries. Mark UNVERIFIED, don't crash loop.
            duration_ms = int((time.time() - start_time) * 1000)
            logger.warning(
                "react_mcp_tool_failure",
                tool=action.tool_name,
                attempts=mcp_err.attempts,
                error=mcp_err.error_message
            )
            obs = ReActObservation(
                result_summary=(
                    f"UNVERIFIED: MCP tool '{action.tool_name}' failed after "
                    f"{mcp_err.attempts} attempt(s): {mcp_err.error_message}"
                ),
                data={"error": mcp_err.error_message, "tool": action.tool_name, "attempts": mcp_err.attempts},
                is_error=True,
                duration_ms=duration_ms
            )
            try:
                await stream_manager.broadcast(self.investigation_id, "tool_call_completed", {
                    "agent_name": self.agent_name,
                    "tool_name": action.tool_name,
                    "mcp_server": mcp_server,
                    "arguments": action.arguments,
                    "result_status": "UNVERIFIED",
                    "duration_ms": duration_ms,
                    "result_summary": obs.result_summary,
                    "retry_count": mcp_err.attempts,
                })
            except Exception:
                pass
            return obs
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.warning("react_tool_execution_failed", tool=action.tool_name, error=str(e))
            obs = ReActObservation(
                result_summary=f"Tool execution failed: {str(e)}",
                data={"error": str(e)},
                is_error=True,
                duration_ms=duration_ms
            )

            try:
                await stream_manager.broadcast(self.investigation_id, "tool_call_completed", {
                    "agent_name": self.agent_name,
                    "tool_name": action.tool_name,
                    "mcp_server": mcp_server,
                    "arguments": action.arguments,
                    "result_status": "ERROR",
                    "duration_ms": duration_ms,
                    "result_summary": f"Tool execution failed: {str(e)}",
                    "retry_count": 0
                })
            except Exception:
                pass

            return obs

    def record_step(self, iteration: int, rationale: str, action: ReActAction, observation: ReActObservation):
        step = ReActStep(
            iteration=iteration,
            rationale=rationale,
            action=action,
            observation=observation
        )
        self.steps.append(step)
        logger.info(
            "react_step_completed",
            agent=self.agent_name,
            iteration=iteration,
            tool=action.tool_name,
            duration_ms=observation.duration_ms
        )
