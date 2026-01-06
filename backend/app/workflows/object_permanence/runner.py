from loguru import logger

from app.core.db import get_session
from app.shared.frame_broadcaster import FrameBroadcaster
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DetectedObject
from app.workflows.object_permanence.workflow import create_compiled_state_graph


async def object_permanence_workflow_runner(broadcaster: FrameBroadcaster):
    logger.info("Starting service_runner loop.")
    last_processed_version = -1
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
            async for db_session in get_session():
                logger.debug(f"Invoking workflow state graph for version {version}.")
                initial_state = ObjectPermanenceWorkflowState(current_frame_b64=frame,
                                                              previous_frame_objects=previous_frame_objects,
                                                              previous_room=previous_room,
                                                              db_session=db_session)
                workflow = create_compiled_state_graph()
                final_state = await workflow.ainvoke(initial_state)

                # Update state for the next iteration
                previous_frame_objects = final_state.previous_frame_objects
                if final_state.current_analysis:
                    previous_room = final_state.current_analysis.scene.room_name

                logger.success(f"Successfully processed frame version {version}.")
                last_processed_version = version
                break  # Exit session scope after one successful run

        except Exception as e:
            logger.error(f"Error processing frame version {version}: {e}", exc_info=True)

    logger.warning(f"service_runner loop has terminated because broadcaster.is_running is False.")
