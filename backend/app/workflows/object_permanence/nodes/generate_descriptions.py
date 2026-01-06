from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from loguru import logger

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DescriptionBatch


async def generate_descriptions(state: ObjectPermanenceWorkflowState) -> dict:
    """
    Generate descriptions for a list of unique objects in the current workflow state.

    This function processes the provided state to extract the unique objects and
    formats them into a prompt for a language model. The function interacts with
    a pre-defined model agent to generate descriptions of the objects in a
    token-efficient and structured format. The generated descriptions are then
    mapped back to their respective objects based on their indices.

    :param state: The current workflow state containing objects and analysis
        context required for description generation.
    :type state: ObjectPermanenceWorkflowState
    :return: A dictionary containing a list of generated descriptions, where
        each description corresponds to an object in the input state.
    :rtype: dict
    """
    # Validation: If no objects, skip
    if not state.unique_objects:
        return {"generated_descriptions": []}

    # Format the input for the LLM to be token-efficient
    # We pass the index 'i' so the LLM can map it back in the response
    prompt_input = []
    for i, obj in enumerate(state.unique_objects):
        prompt_input.append({
            "index": i,
            "name": obj.object_name,
            "visuals": obj.visual_description,
            "landmarks": obj.landmarks
        })

    # Invoke
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )

    agent = create_agent(
        model=model,
        response_format=DescriptionBatch,
        system_prompt=SystemMessage(
            content=Prompts.GENERATE_DESCRIPTIONS
        ),
    )

    response: DescriptionBatch = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Global Room: {state.current_analysis.scene.room_name}\nObjects to Describe: {prompt_input}"
                }
            ]
        }
    )
    response: DescriptionBatch = response["structured_response"]

    desc_map = {d.object_index: d.searchable_text for d in response.descriptions}
    final_texts = [desc_map.get(i, "") for i in range(len(state.unique_objects))]

    logger.info(f"-> Generated {len(final_texts)} descriptions.")
    return {"generated_descriptions": final_texts}
