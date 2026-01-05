import asyncio

from loguru import logger

from app.shared.frame_broadcaster import frame_broadcaster
from app.workflows.object_permanence.state import ObjectPermanenceAnalysis, ObjectPermanenceState
from app.workflows.object_permanence.workflow import create_compiled_state_graph


async def object_permanence_worker():
    graph = create_compiled_state_graph()

    subscriber_id = frame_broadcaster.subscribe("object_permanence_worker")

    analyses_buffer: list[ObjectPermanenceAnalysis] = []

    while True:
        try:
            initial_state = ObjectPermanenceState(
                subscriber_id=subscriber_id,
                frame=frame_broadcaster.get_frame(subscriber_id),
                past_analyses=analyses_buffer
            )

            final_state: ObjectPermanenceState = await graph.ainvoke(initial_state)
            analyses_buffer = final_state.filtered_analyses
            analyses_buffer.append(final_state.analysis)

            await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Error occurred in object_permanence_worker: {e}")
            await asyncio.sleep(1)
