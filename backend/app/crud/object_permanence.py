from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.object_permanence import ObjectPermanence


async def create_log_entry(
        db: AsyncSession,
        timestamp: float,
        name: str,
        description: str,
        location: str,
        landmarks: list[str],
        confidence: str,
        formatted_description: str,
        embedding: list[float]
):
    """
    Creates and saves a new log entry for an object's state in the database.
    This function takes detailed information about a detected object, creates an
    ObjectPermanence instance, adds it to the database session, commits the transaction,
    and refreshes the instance to reflect the newly created entry.

    :param db: The database session to use for the transaction.
    :param timestamp: The timestamp of the log entry.
    :param name: The name of the object.
    :param description: A detailed description of the object.
    :param location: The location of the object.
    :param landmarks: A list of landmarks near the object.
    :param confidence: The confidence level of the detection.
    :param formatted_description: A formatted description for vector searches.
    :param embedding: The embedding of the formatted description.
    :return: The newly created ObjectPermanence instance.
    """
    logger.info(f"Creating log entry for object: {name}")
    logger.debug(f"Object details: name={name}, description={description}, location={location}, confidence={confidence}")

    try:
        db_log = ObjectPermanence(
            timestamp=timestamp,
            name=name,
            description=description,
            location=location,
            landmarks=landmarks,
            confidence=confidence,
            formatted_description=formatted_description,
            embedding=embedding
        )
        logger.trace("ObjectPermanence instance created.")

        db.add(db_log)
        logger.trace("Log entry added to the session.")

        await db.commit()
        logger.debug("Log entry committed to the database.")

        await db.refresh(db_log)
        logger.trace("Log entry refreshed from the database.")

        logger.info(f"Successfully created log entry for object: {name} with id: {db_log.id}")
        return db_log

    except Exception as e:
        logger.error(f"Failed to create log entry for object: {name}. Error: {e}")
        await db.rollback()
        logger.info("Database transaction rolled back.")
        raise
