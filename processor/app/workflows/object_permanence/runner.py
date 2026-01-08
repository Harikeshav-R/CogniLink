from loguru import logger

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
    logger.info("Starting object permanence workflow runner loop.")
    last_processed_version = 0
    previous_frame_objects: list[DetectedObject] = []
    previous_room: str | None = None
    logger.trace(
        f"Initial runner state: last_processed_version={last_processed_version}, previous_frame_objects=[], previous_room=None")

    while broadcaster.is_running:
        logger.debug(f"Waiting for new frame (last processed version: {last_processed_version})...")
        frame, version = await broadcaster.get_latest_frame(last_processed_version)

        if not broadcaster.is_running:
            logger.info("Broadcaster stopped while waiting for a frame. Exiting runner loop.")
            break

        if frame is None:
            logger.warning(f"Received a null frame from broadcaster for version {version}. Skipping this iteration.")
            last_processed_version = version
            continue

        logger.info(f"New frame received (version: {version}). Starting workflow execution.")
        try:
            logger.debug("Acquired new database session for this workflow run.")
            logger.trace(f"Compiling workflow state graph for version {version}.")
            workflow = create_compiled_state_graph()

            initial_state = ObjectPermanenceWorkflowState(
                current_frame_b64=frame,
                previous_frame_objects=previous_frame_objects,
                previous_room=previous_room,
            )
            logger.trace(
                f"Initial workflow state prepared for version {version}: {initial_state.model_dump(exclude={'db_session', 'current_frame_b64'})}")

            logger.debug(f"Invoking workflow for frame version {version}...")
            final_state_raw = await workflow.ainvoke(initial_state)
            final_state = ObjectPermanenceWorkflowState.model_validate(final_state_raw)
            logger.debug(f"Workflow for version {version} completed.")
            logger.trace(
                f"Final workflow state: {final_state.model_dump(exclude={'db_session', 'current_frame_b64'})}")

            # Update state for the next iteration
            logger.trace("Updating runner state for next iteration...")
            if final_state:
                previous_frame_objects = final_state.previous_frame_objects
                logger.trace(f"Updated previous_frame_objects with {len(previous_frame_objects)} objects.")
                current_analysis = final_state.current_analysis
                if current_analysis:
                    previous_room = current_analysis.scene.room_name
                    logger.trace(f"Updated previous_room to '{previous_room}'.")
                else:
                    logger.trace("No current analysis in final state, previous_room remains unchanged.")
            else:
                logger.warning("Workflow returned a null or invalid final_state. Runner state will not be updated.")

            logger.success(f"Successfully processed and concluded workflow for frame version {version}.")
            last_processed_version = version

        except Exception as e:
            logger.error(f"An unhandled error occurred while processing frame version {version}: {e}", exc_info=True,
                         backtrace=True)
            # Optional: decide whether to break the loop or continue on error
            # For robustness, we'll log and continue to the next frame.
            last_processed_version = version

    logger.warning("Object permanence workflow runner loop has terminated because broadcaster.is_running is False.")
