from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Config

logger.trace("Attempting to create database engine.")
# Hiding password in the log
safe_postgres_url = Config.POSTGRES_URL.replace(Config.POSTGRES_PASSWORD, "****")
logger.info(f"Creating database engine with URL: {safe_postgres_url}")
engine = create_async_engine(Config.POSTGRES_URL)
logger.success("Database engine created successfully.")


async def init_db() -> None:
    """
    Initializes the database by creating tables and enabling necessary extensions.

    It enables the 'vector' extension for pgvector support and creates all tables
    defined by SQLModel metadata.

    :return: None
    :rtype: None
    """
    logger.info("Starting database initialization...")
    try:
        async with engine.begin() as conn:
            logger.debug("Transaction started for database initialization.")

            logger.trace("Executing command: CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("Ensured 'vector' extension is enabled.")

            logger.debug("Creating all tables based on SQLModel metadata...")
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("All tables created or verified successfully.")

            logger.debug("Committing transaction for database initialization.")
        logger.success("Database initialization complete.")
    except Exception as e:
        logger.error(f"Failed during database initialization: {e}", exc_info=True)
        raise


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous generator that provides a database session.

    It creates a new AsyncSession for each call, yields it for use in a `with` block,
    and ensures that the session is properly closed (or rolled back on error) after use.

    :return: An asynchronous generator yielding a database session.
    :rtype: AsyncGenerator[AsyncSession, None]
    """
    logger.debug("Request for a new database session received.")
    session: AsyncSession | None = None
    try:
        logger.trace("Creating new AsyncSession from engine.")
        session = AsyncSession(engine)
        logger.debug("New database session created. Yielding to context.")
        yield session
        logger.trace("Context finished. Session is about to be closed.")
    except Exception as e:
        logger.error(f"An exception occurred within the session context: {e}", exc_info=True)
        if session:
            logger.warning("Rolling back the transaction due to an exception.")
            await session.rollback()
        raise
    finally:
        if session:
            logger.debug("Closing database session.")
            await session.close()
            logger.trace("Session closed.")
