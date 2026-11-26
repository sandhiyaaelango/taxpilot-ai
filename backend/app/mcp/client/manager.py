import json
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.config.settings import settings
from app.config.logging import get_logger
from app.mcp.servers.tax_portal_server import (
    app as tax_portal_app,
    TAX_PORTAL_TOOLS,
    execute_get_notice,
    execute_get_filed_returns,
    execute_get_return_details,
    execute_get_vendor_filing_status,
)
from app.mcp.servers.ledger_server import (
    app as ledger_app,
    LEDGER_TOOLS,
    execute_get_entries_by_period,
    execute_get_invoice_details,
    execute_search_invoices,
    execute_get_ledger_records,
)

logger = get_logger("mcp_client_manager")

TAX_TOOL_EXECUTORS = {
    "get_notice": execute_get_notice,
    "get_filed_returns": execute_get_filed_returns,
    "get_return_details": execute_get_return_details,
    "get_vendor_filing_status": execute_get_vendor_filing_status,
}

LEDGER_TOOL_EXECUTORS = {
    "get_entries_by_period": execute_get_entries_by_period,
    "get_invoice_details": execute_get_invoice_details,
    "search_invoices": execute_search_invoices,
    "get_ledger_records": execute_get_ledger_records,
}


class MCPToolFailure(Exception):
    """
    Raised when an MCP tool call fails after exhausting all retries.

    Attributes:
        tool_name     — Name of the failed MCP tool.
        error_message — Human-readable description of the failure.
        attempts      — Number of attempts made (including the first).
    """
    def __init__(self, tool_name: str, error_message: str, attempts: int):
        super().__init__(f"MCP tool '{tool_name}' failed after {attempts} attempt(s): {error_message}")
        self.tool_name = tool_name
        self.error_message = error_message
        self.attempts = attempts


class MCPToolDefinition:
    def __init__(self, name: str, description: str, server_name: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.server_name = server_name
        self.input_schema = input_schema

class MCPClientManager:
    """
    Enterprise MCP Client Manager.

    Supports both network HTTP and in-process execution with fast fallback.

    NOTE ON MOCK DATA:
    ------------------
    The Tax Portal MCP server and Ledger MCP server currently use *mock data*
    (see app/mcp/servers/tax_portal_server.py and ledger_server.py).
    They are designed to be replaced with real HTTP calls to the GST Tax Portal
    and an enterprise ledger system without changing this manager's interface.

    Real integration path:
      1. Set `self._server_available[server_name] = True` once the daemon is running.
      2. The HTTP path in `invoke_tool` will be used automatically.
      3. The in-process path remains as a fallback for local testing.
    """
    def __init__(self):
        self.tax_portal_url = f"http://{settings.tax_portal_mcp_host}:{settings.tax_portal_mcp_port}"
        self.ledger_url = f"http://{settings.ledger_mcp_host}:{settings.ledger_mcp_port}"
        self._tools_cache: Dict[str, MCPToolDefinition] = {}
        self._initialized = False
        self._server_available: Dict[str, bool] = {"tax_portal": False, "ledger": False}

    async def initialize(self) -> None:
        """Discover tools from both MCP servers."""
        self._tools_cache.clear()
        
        # Discover Tax Portal MCP Tools
        tax_tools = await self._discover_server_tools("tax_portal", self.tax_portal_url, tax_portal_app)
        for t in tax_tools:
            self._tools_cache[t.name] = t

        # Discover Ledger MCP Tools
        ledger_tools = await self._discover_server_tools("ledger", self.ledger_url, ledger_app)
        for t in ledger_tools:
            self._tools_cache[t.name] = t

        self._initialized = True
        logger.info("mcp_client_initialized", total_tools=len(self._tools_cache))

    async def _discover_server_tools(self, server_name: str, base_url: str, asgi_app: Any) -> List[MCPToolDefinition]:
        """Query tools/list via instant in-process definitions."""
        tools = TAX_PORTAL_TOOLS if server_name == "tax_portal" else LEDGER_TOOLS
        return [MCPToolDefinition(t["name"], t["description"], server_name, t.get("inputSchema", {})) for t in tools]

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "server": t.server_name,
                "inputSchema": t.input_schema
            }
            for t in self._tools_cache.values()
        ]

    async def invoke_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        max_retries: int = 3,
        timeout_seconds: float = 5.0
    ) -> Dict[str, Any]:
        """
        Invoke an MCP tool with retry and exponential backoff.

        Retry policy (Phase 4 — MCP Reliability):
        - Retries on TimeoutError and ConnectionError (transient failures).
        - Non-retriable errors (ValueError, RuntimeError from bad data) fail immediately.
        - Backoff: attempt 0 → 0s, attempt 1 → 0.5s, attempt 2 → 1s, attempt 3 → 2s.
        - Raises MCPToolFailure after exhausting all retries.

        Args:
            tool_name:       MCP tool identifier.
            arguments:       Tool input dict.
            max_retries:     Maximum number of retry attempts (default 3; 4 total calls).
            timeout_seconds: Per-call timeout for HTTP path only.

        Returns:
            Tool result dict.

        Raises:
            MCPToolFailure: After max_retries + 1 failed attempts.
            ValueError:     If tool_name is not registered.
        """
        if not self._initialized:
            await self.initialize()

        tool_def = self._tools_cache.get(tool_name)
        if not tool_def:
            raise ValueError(f"Tool '{tool_name}' not registered in any connected MCP server")

        server_name = tool_def.server_name
        base_url = self.tax_portal_url if server_name == "tax_portal" else self.ledger_url

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": int(datetime.now(timezone.utc).timestamp() * 1000)
        }

        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            # Exponential backoff before each retry (not before first attempt)
            if attempt > 0:
                backoff_seconds = 0.5 * (2 ** (attempt - 1))  # 0.5s, 1s, 2s
                logger.info(
                    "mcp_tool_retry",
                    tool=tool_name,
                    attempt=attempt,
                    backoff_seconds=backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)

            try:
                # HTTP path: used when daemon is running and flagged available
                if self._server_available.get(server_name, False):
                    try:
                        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                            response = await client.post(f"{base_url}/mcp", json=payload)
                            if response.status_code == 200:
                                result = self._parse_mcp_response(response.json(), tool_name)
                                if attempt > 0:
                                    logger.info("mcp_tool_retry_succeeded", tool=tool_name, attempt=attempt)
                                return result
                    except (httpx.TimeoutException, httpx.ConnectError) as http_err:
                        self._server_available[server_name] = False
                        last_error = http_err
                        logger.warning("mcp_http_path_failed_fallback", tool=tool_name, error=str(http_err))
                        # Fall through to in-process

                # In-process direct execution (mock / local fallback)
                executors = TAX_TOOL_EXECUTORS if server_name == "tax_portal" else LEDGER_TOOL_EXECUTORS
                executor = executors.get(tool_name)
                if executor:
                    result = executor(arguments)
                    if attempt > 0:
                        logger.info("mcp_tool_retry_succeeded_inprocess", tool=tool_name, attempt=attempt)
                    return result

                raise ValueError(f"No in-process executor for tool '{tool_name}'")

            except (TimeoutError, ConnectionError, asyncio.TimeoutError) as transient_err:
                # Retriable transient errors
                last_error = transient_err
                logger.warning(
                    "mcp_tool_transient_error",
                    tool=tool_name,
                    attempt=attempt,
                    error=str(transient_err),
                )
                if attempt < max_retries:
                    continue
                # Last attempt failed — raise MCPToolFailure
                raise MCPToolFailure(tool_name, str(transient_err), attempt + 1) from transient_err

            except ValueError:
                # Non-retriable: tool not found
                raise

            except RuntimeError as mcp_err:
                # Non-retriable: MCP returned a structured error (bad data, not transient)
                raise MCPToolFailure(tool_name, str(mcp_err), attempt + 1) from mcp_err

            except Exception as unexpected:
                # Unexpected error — treat as non-retriable to avoid infinite loops
                logger.error("mcp_tool_unexpected_error", tool=tool_name, error=str(unexpected), exc_info=True)
                raise MCPToolFailure(tool_name, str(unexpected), attempt + 1) from unexpected

        # Should not reach here, but safeguard
        raise MCPToolFailure(tool_name, str(last_error) if last_error else "Unknown", max_retries + 1)

    def _parse_mcp_response(self, data: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        if "error" in data:
            err = data["error"]
            raise RuntimeError(f"MCP Error ({err.get('code')}): {err.get('message')}")

        result = data.get("result", {})
        if result.get("isError"):
            content = result.get("content", [{}])[0].get("text", "Unknown MCP tool error")
            raise RuntimeError(f"MCP tool '{tool_name}' reported error: {content}")

        content_list = result.get("content", [])
        if not content_list:
            return {}

        text_content = content_list[0].get("text", "{}")
        try:
            return json.loads(text_content)
        except Exception:
            return {"raw_text": text_content}

mcp_client = MCPClientManager()
