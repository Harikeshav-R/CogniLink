import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from loguru import logger

from app.shared.frame_broadcaster import frame_broadcaster
from app.workflows.object_permanence.state import ObjectPermanenceState, ObjectPermanenceObject
from app.workflows.object_permanence.workflow import create_compiled_state_graph


async def object_permanence_worker(db_session: AsyncSession):
    graph = create_compiled_state_graph()

    subscriber_id = frame_broadcaster.subscribe("object_permanence_worker")

    analyses_buffer: list[ObjectPermanenceObject] = []

    while True:
        try:
            initial_state = ObjectPermanenceState(
                subscriber_id=subscriber_id,
                db_session=db_session,
                frame=frame_broadcaster.get_frame(subscriber_id),
                past_analyses=analyses_buffer
            )

            final_state: ObjectPermanenceState = await graph.ainvoke(initial_state)
            analyses_buffer = final_state.analyses_buffer

            await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Error occurred in object_permanence_worker: {e}")
            raise
