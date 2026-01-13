from typing import Optional

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User


async def create_user(
        db: AsyncSession,
        first_name: str,
        last_name: str,
        face_embedding: Optional[list[float]] = None
) -> User:
    logger.trace("Instantiating User model...")
    db_user = User(
        first_name=first_name,
        last_name=last_name,
        face_embedding=face_embedding
    )
    logger.trace("User instance created: {}", db_user)

    logger.trace("Adding new User instance to the session.")
    db.add(db_user)

    try:
        logger.debug("Committing transaction to database...")
        await db.commit()
        logger.trace("Commit successful.")

        logger.debug("Refreshing instance from database to retrieve generated fields (e.g., ID).")
        await db.refresh(db_user)
        logger.trace("Instance refreshed: {}", db_user)

        logger.success("Successfully created user entry with ID: {}", db_user.id)
    except Exception as e:
        logger.error("Failed to create user entry.", exc_info=True)
        logger.trace("Rolling back transaction...")
        await db.rollback()
        raise e

    logger.trace("Returning created user entry.")
    return db_user
