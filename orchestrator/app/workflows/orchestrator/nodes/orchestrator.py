from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from loguru import logger

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.orchestrator.prompts import Prompts
from app.workflows.orchestrator.schemas import OrchestratorWorkflowState, SelectedWorkflow


async def orchestrator(state: OrchestratorWorkflowState) -> dict:
    """
    Handles the orchestration of a workflow by invoking an AI model with input
    query and returning a structured response encapsulating the selected workflow.

    :param state: The current state of the orchestrator containing necessary
        information such as the query to be processed.
    :type state: OrchestratorWorkflowState

    :return: A dictionary containing the selected workflow from the AI model's
        structured response.
    :rtype: dict
    """
    logger.info("Orchestrating user query to select the appropriate workflow.")
    logger.debug(f"Current state: {state}")

    logger.trace("Initializing Pollinations chat model.")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_FAST_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.trace("Model initialized.")

    logger.trace("Creating agent with response format and system prompt.")
    agent = create_agent(
        model=model,
        response_format=SelectedWorkflow,
        system_prompt=SystemMessage(
            content=Prompts.ORCHESTRATOR
        ),
    )
    logger.trace("Agent created.")

    logger.debug(f"Invoking agent with query: '{state.query}'")
    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": state.query}
                    ]
                }
            ]
        }
    )
    logger.debug("Agent invocation complete.")
    logger.trace(f"Response from agent: {response}")

    structured_response: SelectedWorkflow = response["structured_response"]
    logger.success(f"Workflow selected: {structured_response.workflow}")

    final_response = {"selected_workflow": structured_response}
    logger.trace(f"Returning final response: {final_response}")
    return final_response

