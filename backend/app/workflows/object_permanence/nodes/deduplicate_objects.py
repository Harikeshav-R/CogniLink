from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from loguru import logger

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DeduplicationResult, DetectedObject


async def deduplicate_objects(state: ObjectPermanenceWorkflowState) -> dict:
    """
    Deduplicates objects between the current and previous frame of analysis in a scene, identifying
    unique objects and updating the state with the deduplication results. This function uses
    an external Large Language Model (LLM) to assist in determining uniqueness of objects based on
    their properties.

    :param state: The current workflow state containing details about the current frame's analysis,
        previous frame's objects, and room context.
    :type state: ObjectPermanenceWorkflowState

    :return: A dictionary containing:
        - "unique_objects": A list of objects identified as unique in the current analysis.
        - "previous_frame_objects": The updated list of previous frame's objects for reference.
        - "previous_room": The room name of the current analysis to track contextual changes.
    :rtype: dict
    """
    logger.trace("Entering 'deduplicate_objects' node.")
    if not state.current_analysis:
        logger.warning("No current analysis found in state. Skipping deduplication.")
        return {"unique_objects": []}

    if not state.previous_frame_objects:
        logger.info("No previous objects found in state. All current objects are considered unique.")
        unique_objects = state.current_analysis.objects
        logger.debug(f"Found {len(unique_objects)} unique objects.")
        return {
            "unique_objects": unique_objects,
            "previous_frame_objects": unique_objects,
            "previous_room": state.current_analysis.scene.room_name,
        }

    logger.debug(f"Comparing {len(state.current_analysis.objects)} current objects against {len(state.previous_frame_objects)} previous objects.")
    logger.trace(f"Previous room: '{state.previous_room}', Current room: '{state.current_analysis.scene.room_name}'")

    # 2. Prepare Data for LLM (Stripped down to save tokens)
    def prep(objs):
        return [
            {"i": i, "name": o.object_name, "loc": o.landmarks, "vis": o.visual_description, "xy": o.location_coords}
            for i, o in enumerate(objs)]

    prompt = f"""
    PREV ROOM: {state.previous_room}
    CURR ROOM: {state.current_analysis.scene.room_name}

    PREV OBJECTS: {prep(state.previous_frame_objects)}
    CURR OBJECTS: {prep(state.current_analysis.objects)}
    """
    logger.trace(f"Generated prompt for deduplication agent:\n{prompt}")

    logger.debug("Initializing model for deduplication...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.trace("Model initialized.")

    logger.debug("Creating deduplication agent with structured output (DeduplicationResult).")
    agent = create_agent(
        model=model,
        response_format=DeduplicationResult,
        system_prompt=SystemMessage(
            content=Prompts.DEDUPLICATE_NODES
        ),
    )
    logger.trace("Deduplication agent created.")

    logger.debug("Invoking agent for deduplication decision...")
    decision_response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }
    )
    logger.trace(f"Agent invocation complete. Full response: {decision_response}")
    decision: DeduplicationResult = decision_response["structured_response"]
    logger.debug(f"Agent decision: '{decision.reasoning}', Unique indices: {decision.unique_object_indices}")

    # 4. Filter
    unique_objs: list[DetectedObject] = []
    max_index = len(state.current_analysis.objects)
    logger.debug(f"Filtering unique objects based on agent response. Max index is {max_index - 1}.")
    for i in decision.unique_object_indices:
        if 0 <= i < max_index:
            logger.trace(f"Index {i} is valid. Appending object to unique list.")
            unique_objs.append(state.current_analysis.objects[i])
        else:
            logger.warning(f"LLM returned an invalid index {i}, which is out of bounds for current objects list (size={max_index}). Ignoring.")

    if unique_objs:
        logger.info(f"Deduplication resulted in {len(unique_objs)} unique objects. Reason: {decision.reasoning}")
    else:
        logger.info("Deduplication found no unique objects. All current objects are considered duplicates.")

    logger.trace("Exiting 'deduplicate_objects' node.")
    return {
        "unique_objects": unique_objs,
        "previous_frame_objects": state.current_analysis.objects,  # Update history
        "previous_room": state.current_analysis.scene.room_name,
    }
