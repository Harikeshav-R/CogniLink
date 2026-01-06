from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Config

logger.info(f"Creating database engine with URL.")
engine = create_async_engine(Config.POSTGRES_URL)
logger.info("Database engine created successfully.")


async def init_db() -> None:
    """
    Initializes the database by creating tables and enabling necessary extensions.

    It enables the 'vector' extension for pgvector support and creates all tables
    defined by SQLModel metadata.

    :return: None
    :rtype: None
    """
    logger.info("Initializing the database...")
    async with engine.begin() as conn:
        logger.debug("Enabling 'vector' extension if not exists...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("'vector' extension enabled.")

        logger.debug("Creating all tables from SQLModel metadata...")
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("All tables created successfully.")
    logger.info("Database initialization complete.")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous generator that provides a database session.

    It creates a new AsyncSession for each call and yields it, ensuring that
    the session is properly closed after use.

    :return: An asynchronous generator yielding a database session.
    :rtype: AsyncGenerator[AsyncSession, None]
    """
    logger.debug("Creating new database session.")
    async with AsyncSession(engine) as session:
        try:
            logger.debug("Yielding database session.")
            yield session
        finally:
            logger.debug("Database session closed.")
