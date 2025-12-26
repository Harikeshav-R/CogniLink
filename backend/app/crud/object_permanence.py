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
    db_log = ObjectPermanence(
        content=content,
        embedding=embedding,
        timestamp=timestamp,
        object_name=object_name,
        log_type=log_type
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return db_log
