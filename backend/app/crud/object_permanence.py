from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.models.object_permanence import ObjectPermanence


async def create_log_entry(
        db: AsyncSession,
        timestamp: float,
        object_name: str,
        description: str,
        embedding: list[float]
):
    logger.info("Creating new object permanence log entry for object: '{}'", object_name)
    logger.debug("Log details - Timestamp: {}, Description length: {}, Embedding size: {}", 
                 timestamp, len(description), len(embedding))

    db_log = ObjectPermanence(
        timestamp=timestamp,
        object_name=object_name,
        description=description,
        embedding=embedding
    )
    
    logger.trace("Adding new ObjectPermanence instance to the session.")
    db.add(db_log)
    
    try:
        logger.debug("Committing transaction to database...")
        await db.commit()
        
        logger.debug("Refreshing instance from database to retrieve generated fields (e.g., ID).")
        await db.refresh(db_log)
        
        logger.success("Successfully created log entry with ID: {}", db_log.id)
    except Exception as e:
        logger.exception("Failed to create object permanence log entry.")
        raise e

    return db_log