from fastapi import Request
from fastapi.responses import JSONResponse
from app.config.logging import get_logger

logger = get_logger(__name__)

class TaxPilotException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(TaxPilotException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} with id '{resource_id}' not found", "NOT_FOUND", 404)

class AuthenticationError(TaxPilotException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)

class AuthorizationError(TaxPilotException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)

class ValidationError(TaxPilotException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)

class InvestigationError(TaxPilotException):
    def __init__(self, message: str):
        super().__init__(message, "INVESTIGATION_ERROR", 500)

class MCPConnectionError(TaxPilotException):
    def __init__(self, server: str, message: str):
        super().__init__(f"MCP server '{server}' error: {message}", "MCP_CONNECTION_ERROR", 503)

async def taxpilot_exception_handler(request: Request, exc: TaxPilotException) -> JSONResponse:
    logger.warning("application_error", code=exc.code, message=exc.message, path=str(request.url))
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.code, "message": exc.message}}
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}
    )
