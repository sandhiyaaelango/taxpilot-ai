import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.config.logging import setup_logging, get_logger
from app.core.exceptions import TaxPilotException, taxpilot_exception_handler, generic_exception_handler
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.api.v1.router import api_router
from app.mcp.client.manager import mcp_client

setup_logging(settings.log_level)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("taxpilot_startup", env=settings.app_env, version="1.0.0")
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Ensure database schema is initialized
    try:
        from app.database.session import async_engine
        from app.database.base import Base
        import app.database.models  # noqa: F401
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.warning("database_schema_init_warning", error=str(e))

    try:
        await mcp_client.initialize()
    except Exception as e:
        logger.warning("mcp_startup_init_failed", error=str(e))
    yield
    # Shutdown
    logger.info("taxpilot_shutdown")

app = FastAPI(
    title="TaxPilot AI API",
    description="Agentic AI-Powered GST Notice Investigation & Evidence Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(TaxPilotException, taxpilot_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TaxPilot AI", "version": "1.0.0"}

# Serve uploaded files if dir exists
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
