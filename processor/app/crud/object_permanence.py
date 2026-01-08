from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.object_permanence import ObjectPermanence


async def create_object_permanence_entry(
        db: AsyncSession,
        timestamp: float,
        object_name: str,
        description: str,
        embedding: list[float]
) -> ObjectPermanence:
    """
    Create a new object permanence log entry in the database.

    This function instantiates an ObjectPermanence model, persists it to the database,
    and handles transaction commits and rollbacks.

    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param timestamp: The Unix timestamp when the object was observed.
    :type timestamp: float
    :param object_name: The name or identifier of the object.
    :type object_name: str
    :param description: A textual description of the object or its state.
    :type description: str
    :param embedding: A vector representation (embedding) of the object.
    :type embedding: list[float]
    :return: The created object permanence database record, including generated fields like ID.
    :rtype: ObjectPermanence
    :raises Exception: If the database transaction fails, the session is rolled back and the exception is re-raised.
    """

    logger.info("Creating new object permanence log entry for object: '{}'", object_name)
    logger.debug("Log details - Timestamp: {}, Description length: {}, Embedding size: {}",
                 timestamp, len(description), len(embedding))

    logger.trace("Instantiating ObjectPermanence model...")
    db_log = ObjectPermanence(
        timestamp=timestamp,
        object_name=object_name,
        description=description,
        embedding=embedding
    )
    logger.trace("ObjectPermanence instance created: {}", db_log)

    logger.trace("Adding new ObjectPermanence instance to the session.")
    db.add(db_log)

    try:
        logger.debug("Committing transaction to database...")
        await db.commit()
        logger.trace("Commit successful.")

        logger.debug("Refreshing instance from database to retrieve generated fields (e.g., ID).")
        await db.refresh(db_log)
        logger.trace("Instance refreshed: {}", db_log)

        logger.success("Successfully created log entry with ID: {}", db_log.id)
    except Exception as e:
        logger.error("Failed to create object permanence log entry.", exc_info=True)
        logger.trace("Rolling back transaction...")
        await db.rollback()
        raise e

    logger.trace("Returning created log entry.")
    return db_log
