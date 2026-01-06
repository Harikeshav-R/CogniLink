from loguru import logger

from app.core.db import get_session
from app.shared.frame_broadcaster import FrameBroadcaster
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DetectedObject
from app.workflows.object_permanence.workflow import create_compiled_state_graph


async def object_permanence_workflow_runner(broadcaster: FrameBroadcaster) -> None:
    """
    Asynchronous function to execute the object permanence workflow in a continuous loop, processing
    frames from a `FrameBroadcaster`. This function performs a stateful analysis of successive video
    frames, leveraging a workflow state graph for structured processing. It maintains records of
    processed versions, previously detected objects, and the last analyzed room for continuity
    between frames. The loop continues execution while the `broadcaster.is_running` is set to True.

    :param broadcaster: The instance of `FrameBroadcaster` providing video frames for processing.
    :type broadcaster: FrameBroadcaster
    :return: Coroutine that runs the object permanence workflow loop.
    :rtype: Coroutine
    """
    logger.info("Starting service_runner loop.")
    last_processed_version = 0
    previous_frame_objects: list[DetectedObject] = []
    previous_room: str | None = None

    while broadcaster.is_running:
        logger.debug(f"Waiting for frame version newer than {last_processed_version}...")
        frame, version = await broadcaster.get_latest_frame(last_processed_version)

        if not broadcaster.is_running:
            logger.info(f"Broadcaster stopped while waiting for frame. Exiting service_runner.")
            break

        logger.info(f"New frame detected (version: {version}). Starting workflow execution.")
        try:
            # Create a new session for each workflow execution
            async with get_session() as db_session:
                logger.debug(f"Invoking workflow state graph for version {version}.")
                initial_state = ObjectPermanenceWorkflowState(current_frame_b64=frame,
                                                              previous_frame_objects=previous_frame_objects,
                                                              previous_room=previous_room,
                                                              db_session=db_session)
                workflow = create_compiled_state_graph()

                logger.debug("Awaiting workflow.ainvoke...")
                final_state: ObjectPermanenceWorkflowState = await workflow.ainvoke(initial_state)
                final_state = ObjectPermanenceWorkflowState.model_validate(final_state)
                logger.debug(f"workflow.ainvoke completed. Final state: {final_state.model_dump(exclude={'db_session', 'current_frame_b64'})}")

                # Update state for the next iteration
                if final_state:
                    previous_frame_objects = final_state.previous_frame_objects
                    current_analysis = final_state.current_analysis
                    if current_analysis:
                        previous_room = current_analysis.scene.room_name
                else:
                    logger.warning("Workflow returned a null final_state.")

                logger.success(f"Successfully processed frame version {version}.")
                last_processed_version = version

        except Exception as e:
            logger.error(f"Error processing frame version {version}: {e}", exc_info=True, backtrace=True)
            raise e

    logger.warning(f"service_runner loop has terminated because broadcaster.is_running is False.")
