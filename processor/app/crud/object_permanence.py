from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.object_permanence import ObjectPermanence


async def create_object_permanence_entry(
        db: AsyncSession,
        timestamp: float,
        object_name: str,
        description: str,
        embedding: list[float]
) -> ObjectPermanence:
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


async def read_object_permanence_entries_by_vector_search(db: AsyncSession, query_vector: list[float],
                                                          limit: int = 10) -> list[
    ObjectPermanence]:
    """
    Performs a vector-based similarity search on the ObjectPermanence entity
    and retrieves a list of entries ordered by proximity to the given query
    vector.

    This method executes a database query to search for objects in the
    `ObjectPermanence` database table. The objects are sorted by the cosine
    distance of their embeddings to the provided `query_vector`, ensuring
    that the closest matches are returned.

    :param db: The asynchronous database session to execute the query.
    :type db: AsyncSession
    :param query_vector: The vector used as the basis for similarity
                         comparison. Each value in the list should represent
                         a numerical dimension.
    :type query_vector: list[float]
    :param limit: Maximum number of entries to retrieve from the query result.
                  Defaults to 10 if not specified.
    :type limit: int
    :return: A list of `ObjectPermanence` objects that are most similar to the
             provided query vector, ordered by increasing cosine distance.
    :rtype: list[ObjectPermanence]
    """
    logger.info("Executing vector similarity search for ObjectPermanence.")
    logger.debug("Search parameters - Query vector size: {}, Limit: {}", len(query_vector), limit)

    logger.trace("Constructing SQL statement with cosine distance ordering.")
    statement = select(ObjectPermanence).order_by(
        ObjectPermanence.embedding.cosine_distance(query_vector)
    ).limit(limit)

    try:
        logger.trace("Executing database query...")
        result = await db.exec(statement)

        logger.trace("Fetching all results from the executable.")
        entries = list(result.all())

        logger.success("Vector search completed. Found {} matching entries.", len(entries))
        return entries
    except Exception as e:
        logger.error("An error occurred during the vector similarity search.", exc_info=True)
        raise e
