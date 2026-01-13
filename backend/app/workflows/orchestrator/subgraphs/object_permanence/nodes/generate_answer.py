import json
from loguru import logger
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model, init_google_genai_chat_model
from app.workflows.orchestrator.subgraphs.object_permanence.prompts import Prompts
from app.workflows.orchestrator.subgraphs.object_permanence.schemas import ObjectPermanenceWorkflowState, GenerateAnswerOutput


async def generate_answer(state: ObjectPermanenceWorkflowState) -> dict:
    """
    Generates an answer based on the current state of an object permanence workflow.

    This function interacts with the LLM to process the messages sent by
    the user and return a structured response. It uses a predefined system prompt
    and a generated agent to invoke the workflow asynchronously. The result is
    a processed output in the form of an answer derived from the user's input and
    the matching entries.

    :param state: An instance of ObjectPermanenceWorkflowState representing the
        current state of the workflow and the matching entries that should be
        included in the response.
    :type state: ObjectPermanenceWorkflowState
    :return: A dictionary containing the generated response derived from the answer
        provided by the structured response.
    :rtype: dict
    """
    logger.info("Generating answer for the object permanence workflow.")
    logger.debug(f"Current state: {state}")

    logger.trace("Initializing Pollinations chat model.")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_FAST_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    # model = init_google_genai_chat_model(
    #     Config.GEMINI_FAST_MODEL,
    #     Config.GEMINI_API_KEY
    # )
    logger.trace("Model initialized.")

    logger.trace("Creating agent with response format and system prompt.")
    agent = create_agent(
        model=model,
        response_format=GenerateAnswerOutput,
        system_prompt=SystemMessage(
            content=Prompts.GENERATE_ANSWER
        ),
    )
    logger.trace("Agent created.")

    logger.debug("Invoking agent with user query and matching entries.")
    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"The query is: {state.query}"},
                        {"type": "text", "text": "Tool output:"},
                        {"type": "text", "text": "\n".join(
                            [json.dumps(entry.model_dump(), indent=2) for entry in state.matching_entries])}
                    ]
                }
            ]
        }
    )
    logger.debug("Agent invocation complete.")
    logger.trace(f"Response from agent: {response}")

    structured_response: GenerateAnswerOutput = response["structured_response"]
    logger.success(f"Answer generated successfully: {structured_response.answer}")
    final_response = {"response": structured_response.answer}
    logger.trace(f"Returning final response: {final_response}")
    return final_response

