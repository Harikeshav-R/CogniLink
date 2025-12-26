from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, TextContentBlock

from app.core.config import Config
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import State, FilteredResults


def filter_results(state: State) -> dict:
    if state.static_analysis is None or state.diff_analysis is None:
        return {}

    model = init_chat_model(
        model=Config.GEMINI_FAST_MODEL,
        model_provider=Config.GEMINI_PROVIDER,
        api_key=Config.GEMINI_API_KEY
    )
    agent = create_agent(
        model=model,
        response_format=FilteredResults,
        system_prompt=SystemMessage(
            content=Prompts.FILTER_RESULTS
        ),
    )

    result = agent.invoke(
        HumanMessage(
            content_blocks=[
                TextContentBlock(
                    type="text",
                    text=Prompts.FILTER_RESULTS
                ),
                TextContentBlock(
                    type="text",
                    text=str(state.static_analysis.model_dump())
                ),
                TextContentBlock(
                    type="text",
                    text=str(state.diff_analysis.model_dump())
                )
            ]
        )
    )

    return {
        "filtered_results": result["structured_output"]
    }
