import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.shared.frame_broadcaster import frame_broadcaster
from app.workflows.object_permanence.state import ObjectPermanenceState, ObjectPermanenceObject
from app.workflows.object_permanence.workflow import create_compiled_state_graph


async def object_permanence_worker(db_session: AsyncSession):
    """
    The main worker for the object permanence workflow.

    It continuously processes video frames to detect and log changes in the
    observed state. It runs in an infinite loop.

    :param db_session: The database session used for saving state changes.
    :type db_session: AsyncSession
    """
    logger.info("Initializing object permanence worker...")
    graph = create_compiled_state_graph()
    logger.debug("Compiled state graph created for the worker.")

    subscriber_id = frame_broadcaster.subscribe("object_permanence_worker")
    logger.info(f"Worker subscribed to frame broadcaster with ID: {subscriber_id}")

    # The worker now owns the "memory" of the last saved state.
    last_saved_analysis: Optional[list[ObjectPermanenceObject]] = None
    logger.debug("Worker's internal memory (last_saved_analysis) initialized to None.")

    while True:
        try:
            logger.trace(f"Worker loop started. Waiting for frame for subscriber: {subscriber_id}")
            frame = frame_broadcaster.get_frame(subscriber_id)
            if not frame:
                await asyncio.sleep(1)
                continue

            logger.info(f"Frame received for subscriber: {subscriber_id}. Processing...")
            logger.trace(f"Frame details: size={frame.size}, mode={frame.mode}")

            initial_state = ObjectPermanenceState(
                subscriber_id=subscriber_id,
                db_session=db_session,
                frame=frame,
                last_saved_analysis=last_saved_analysis
            )
            logger.debug("Initial state created for graph invocation.")
            logger.trace(f"Initial state includes last saved analysis: {bool(last_saved_analysis)}")

            # Invoke the graph
            logger.debug("Invoking state graph with the current frame...")
            final_state: ObjectPermanenceState = await graph.ainvoke(initial_state)
            logger.debug("State graph invocation complete.")
            logger.trace(f"Final state 'save_status': {final_state.save_status}")

            # If the state was changed and saved, update the worker's memory.
            if final_state.save_status:
                logger.info("State was saved. Updating worker's internal memory.")
                last_saved_analysis = final_state.current_analysis
                logger.debug("Worker's 'last_saved_analysis' has been updated.")
            else:
                logger.info("State was not saved. Worker's memory remains unchanged.")

            await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"An error occurred in the object permanence worker loop: {e}", exc_info=True)
            # Depending on the desired resilience, you might want to raise the exception
            # or just log it and continue the loop. The current setup re-raises.
            raise
