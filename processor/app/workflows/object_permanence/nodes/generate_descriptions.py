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
    logger.trace("Entering 'generate_descriptions' node.")
    # Validation: If no objects, skip
    if not state.unique_objects:
        logger.warning("No unique objects in state. Skipping description generation.")
        return {"generated_descriptions": []}

    logger.debug(f"Found {len(state.unique_objects)} unique objects to describe.")

    # Format the input for the LLM to be token-efficient
    # We pass the index 'i' so the LLM can map it back in the response
    logger.trace("Formatting objects into token-efficient prompt input.")
    prompt_input = []
    for i, obj in enumerate(state.unique_objects):
        prompt_input.append({
            "index": i,
            "name": obj.object_name,
            "visuals": obj.visual_description,
            "landmarks": obj.landmarks
        })
    logger.trace(f"Formatted prompt input: {prompt_input}")

    # Invoke
    logger.debug("Initializing model for description generation...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.trace("Model initialized.")

    logger.debug("Creating description generation agent with structured output (DescriptionBatch).")
    agent = create_agent(
        model=model,
        response_format=DescriptionBatch,
        system_prompt=SystemMessage(
            content=Prompts.GENERATE_DESCRIPTIONS
        ),
    )
    logger.trace("Agent created.")

    user_prompt = f"Global Room: {state.current_analysis.scene.room_name}\nObjects to Describe: {prompt_input}"
    logger.trace(f"User prompt for agent: {user_prompt}")

    logger.debug("Invoking agent to generate descriptions...")
    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }
    )
    logger.trace(f"Agent invocation complete. Full response: {response}")

    structured_response: DescriptionBatch = response["structured_response"]
    logger.debug(f"Extracted {len(structured_response.descriptions)} descriptions from agent response.")

    desc_map = {d.object_index: d.searchable_text for d in structured_response.descriptions}
    logger.trace(f"Created description map from response: {desc_map}")

    # Ensure final_texts has the same length as unique_objects, with empty strings for missing descriptions
    final_texts = [desc_map.get(i, "") for i in range(len(state.unique_objects))]
    for i, text in enumerate(final_texts):
        if not text:
            logger.warning(f"Agent did not generate a description for object at index {i}. It will be skipped during save.")

    logger.info(f"Successfully generated {sum(1 for t in final_texts if t)} descriptions for {len(state.unique_objects)} unique objects.")
    logger.trace(f"Final generated descriptions list: {final_texts}")

    logger.trace("Exiting 'generate_descriptions' node.")
    return {"generated_descriptions": final_texts}
