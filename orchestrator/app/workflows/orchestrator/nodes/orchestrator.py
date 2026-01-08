from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.orchestrator.schemas import OrchestratorWorkflowState, SelectedWorkflow


async def orchestrator(state: OrchestratorWorkflowState) -> dict:
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
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
