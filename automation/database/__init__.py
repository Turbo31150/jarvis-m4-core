"""
Database initialization and configuration module
"""

import logging
import asyncio
from pathlib import Path
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration"""

    # Default paths
    DEFAULT_DB_PATH = "automation.db"
    DEFAULT_POOL_SIZE = 5

    # Timeout settings
    CONNECTION_TIMEOUT = 30
    QUERY_TIMEOUT = 60

    # Performance settings
    PAGE_SIZE = 4096
    CACHE_SIZE = -64000  # 64MB


class DatabaseInit:
    """Database initialization utility"""

    def __init__(self, db_path: str = DatabaseConfig.DEFAULT_DB_PATH):
        """Initialize database setup"""
        self.db_path = db_path
        self.manager = DatabaseManager(db_path, pool_size=DatabaseConfig.DEFAULT_POOL_SIZE)

    async def initialize(self):
        """Initialize database"""
        logger.info(f"Initializing database: {self.db_path}")
        await self.manager.initialize()
        logger.info("Database initialized successfully")
        return self.manager

    async def reset(self):
        """Reset database (development only)"""
        if Path(self.db_path).exists():
            Path(self.db_path).unlink()
            logger.warning(f"Database reset: {self.db_path}")
        await self.initialize()

    @staticmethod
    async def get_manager(db_path: str = DatabaseConfig.DEFAULT_DB_PATH) -> DatabaseManager:
        """Get or create database manager"""
        init = DatabaseInit(db_path)
        return await init.initialize()


async def init_database():
    """Initialize database for application startup"""
    manager = await DatabaseInit.get_manager()
    logger.info("Database ready for operations")
    return manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_database())
