from typing import AsyncGenerator

from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Config

engine = create_async_engine(Config.POSTGRES_URL)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 1. Enable the extension using a raw connection
    async with AsyncSession(engine) as session:
        await session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await session.commit()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
