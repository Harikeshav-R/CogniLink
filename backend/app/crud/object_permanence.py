from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.object_permanence import ObjectPermanence


async def create_log_entry(
        db: AsyncSession,
        timestamp: float,
        object_name: str,
        description: str,
        embedding: list[float]
):
    db_log = ObjectPermanence(
        timestamp=timestamp,
        object_name=object_name,
        description=description,
        embedding=embedding
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)

    return db_log