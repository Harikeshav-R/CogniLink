from loguru import logger
from sqlmodel import Session

from app.models.object_permanence import ObjectPermanence


def create_log_entry(
        db: Session,
        content: str,
        embedding: list[float],
        timestamp: float,
        object_name: str,
        log_type: str
):
    """
    Creates and stores a log entry in the database. The log entry includes content,
    embedding data, a timestamp, the associated object name, and its type. The
    entry is committed to the database and the changes are refreshed to ensure the
    latest state of the log entry is returned.

    :param db: The database session used to perform the operation.
    :type db: Session
    :param content: The textual information of the log entry.
    :type content: str
    :param embedding: A list of floating-point numbers representing the embedding
        associated with the log entry.
    :type embedding: list[float]
    :param timestamp: The timestamp indicating when the log entry was created or
        recorded.
    :type timestamp: float
    :param object_name: The name of the object associated with this log entry.
    :type object_name: str
    :param log_type: The type or category of the log entry.
    :type log_type: str
    :return: The newly created log entry after being added to the database.
    :rtype: ObjectPermanence
    """
    logger.info(f"Creating log entry for object: {object_name} of type: {log_type}")
    logger.debug(f"Log entry content: {content}")
    logger.debug(f"Log entry timestamp: {timestamp}")
    db_log = ObjectPermanence(
        content=content,
        embedding=embedding,
        timestamp=timestamp,
        object_name=object_name,
        log_type=log_type
    )
    logger.debug("Log entry object created: {db_log}", db_log=db_log)
    db.add(db_log)
    logger.debug("Log entry added to the database session.")
    db.commit()
    logger.debug("Database session committed.")
    db.refresh(db_log)
    logger.debug("Log entry refreshed from the database.")

    logger.info(f"Successfully created log entry for object: {object_name}")
    return db_log
