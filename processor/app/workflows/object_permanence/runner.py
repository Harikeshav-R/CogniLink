from loguru import logger

from app.shared.frame_broadcaster import FrameBroadcaster
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DetectedObject
from app.workflows.object_permanence.workflow import create_compiled_state_graph


async def object_permanence_workflow_runner(frame_broadcaster: FrameBroadcaster) -> None:
    """
    Executes the object permanence workflow runner using a frame broadcaster.

    This function continuously processes batches of frames obtained from the
    given `frame_broadcaster` and executes an object permanence workflow. The
    workflow analyzes objects across frames to maintain state and
    context information, such as previously analyzed objects and the room
    scene.

    The runner updates its state after each workflow iteration and maintains
    consistency of the analyzed data for downstream processing.

    :param frame_broadcaster: A broadcaster source used to fetch frame batches for processing. It provides a subscription mechanism for frame retrieval.
    :type frame_broadcaster: FrameBroadcaster

    :return: None
    :rtype: None
    """
    frames_subscription = frame_broadcaster.subscribe()
    previous_analyzed_objects: list[DetectedObject] = []
    previous_room: str | None = None

    while True:
        frames: list[str] = await frame_broadcaster.get_strict_batch(frames_subscription, 30)

        try:
            workflow = create_compiled_state_graph()

            initial_state = ObjectPermanenceWorkflowState(
                current_frame_batch_base64=frames,
                previous_frame_objects=previous_analyzed_objects,
                previous_room=previous_room,
            )

            final_state_raw = await workflow.ainvoke(initial_state)
            final_state = ObjectPermanenceWorkflowState.model_validate(final_state_raw)
            logger.trace(
                f"Final workflow state: {final_state.model_dump(exclude={'current_frame_batch_base64'})}")

            # Update state for the next iteration
            logger.trace("Updating runner state for next iteration...")
            if final_state:
                previous_analyzed_objects = final_state.previous_frame_objects
                logger.trace(f"Updated previous_frame_objects with {len(previous_analyzed_objects)} objects.")
                current_analysis = final_state.current_analysis
                if current_analysis:
                    previous_room = current_analysis.scene.room_name
                    logger.trace(f"Updated previous_room to '{previous_room}'.")
                else:
                    logger.trace("No current analysis in final state, previous_room remains unchanged.")
            else:
                logger.warning("Workflow returned a null or invalid final_state. Runner state will not be updated.")

            logger.success(f"Successfully processed and concluded workflow for frame batch.")

        except Exception as e:
            logger.error(
                f"An unhandled error or cancellation occurred while processing frame batch. Type: {type(e)}, Value: {e}",
                exc_info=True,
                backtrace=True)
