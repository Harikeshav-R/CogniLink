import asyncio
import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.shared.frame_broadcaster import frame_broadcaster
from app.workflows.object_permanence.state import ObjectPermanenceState, ObjectPermanenceObject
from app.workflows.object_permanence.workflow import create_compiled_state_graph


async def object_permanence_worker(db_session: AsyncSession):
    graph = create_compiled_state_graph()

    subscriber_id = frame_broadcaster.subscribe("object_permanence_worker")

    # The worker now owns the "memory" of the last saved state.
    last_saved_analysis: Optional[list[ObjectPermanenceObject]] = None

    while True:
        try:
            frame = frame_broadcaster.get_frame(subscriber_id)
            if not frame:
                await asyncio.sleep(1)
                continue

            initial_state = ObjectPermanenceState(
                subscriber_id=subscriber_id,
                db_session=db_session,
                frame=frame,
                last_saved_analysis=last_saved_analysis
            )

            # Invoke the graph
            final_state: ObjectPermanenceState = await graph.ainvoke(initial_state)

            # If the state was changed and saved, update the worker's memory.
            if final_state.save_status:
                last_saved_analysis = final_state.current_analysis

            await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Error occurred in object_permanence_worker: {e}")
            raise
