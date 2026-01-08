from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
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
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_FAST_MODEL,
        Config.POLLINATIONS_API_KEY
    )

    agent = create_agent(
        model=model,
        response_format=SelectedWorkflow,
        system_prompt=SystemMessage(
            content=Prompts.GENERATE_ANSWER
        ),
    )
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

    structured_response: SelectedWorkflow = response["structured_response"]
    return {"selected_workflow": structured_response}
