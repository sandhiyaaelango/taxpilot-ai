import asyncio
from app.database.session import async_engine
from app.database.base import Base
from app.database.models import *  # noqa: F401, F403
from app.config.logging import get_logger

logger = get_logger(__name__)

async def init_database():
    """Create all tables in the database if they don't already exist."""
    async with async_engine.begin() as conn:
        logger.info("creating_database_tables")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("database_tables_created_successfully")

if __name__ == "__main__":
    asyncio.run(init_database())
