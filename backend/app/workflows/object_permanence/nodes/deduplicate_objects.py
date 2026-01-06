from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from loguru import logger

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DeduplicationResult, DetectedObject


async def deduplicate_objects(state: ObjectPermanenceWorkflowState):
    if not state.current_analysis:
        logger.warning("No current analysis found. Skipping deduplication.")
        return {"unique_objects": []}

    if not state.previous_frame_objects:
        logger.info("No previous objects to compare against. All current objects are unique.")
        return {
            "unique_objects": state.current_analysis.objects,
            "previous_frame_objects": state.current_analysis.objects,
            "previous_room": state.current_analysis.scene.room_name
        }

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

    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )

    agent = create_agent(
        model=model,
        response_format=DeduplicationResult,
        system_prompt=SystemMessage(
            content=Prompts.DEDUPLICATE_NODES
        ),
    )

    decision = await agent.ainvoke(
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
    decision: DeduplicationResult = decision["structured_response"]

    # 4. Filter
    unique_objs: list[DetectedObject] = []
    max_index = len(state.current_analysis.objects)
    for i in decision.unique_object_indices:
        if 0 <= i < max_index:
            unique_objs.append(state.current_analysis.objects[i])
        else:
            logger.warning(f"LLM returned an invalid index {i}, which is out of bounds. Ignoring.")

    if unique_objs:
        logger.info(f"Keeping {len(unique_objs)} objects. Reason: {decision.reasoning}")
    else:
        logger.info("All duplicates. Discarding.")

    return {
        "unique_objects": unique_objs,
        "previous_frame_objects": state.current_analysis.objects,  # Update history
        "previous_room": state.current_analysis.scene.room_name
    }
