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
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)

    return db_log
