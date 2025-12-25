import base64

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, TextContentBlock, ImageContentBlock

from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import State, StaticAnalysis


def analyze_static_frame(state: State):
    if state.current_frame is None:
        return {}

    model = init_chat_model(
        model="gemma-3-27b-it",
        model_provider="google_genai"
    )
    agent = create_agent(
        model=model,
        response_format=ProviderStrategy(StaticAnalysis),
        system_prompt=SystemMessage(
            content=Prompts.ANALYZE_STATIC_FRAME
        ),
    )

    result = agent.invoke(
        HumanMessage(
            content_blocks=[
                TextContentBlock(
                    type="text",
                    text=Prompts.ANALYZE_STATIC_FRAME
                ),
                ImageContentBlock(
                    type="image",
                    url=f"data:image/png;base64,{base64.b64encode(state.current_frame.tobytes()).decode("utf-8")}"
                )
            ]
        )
    )

    return {
        "_static_analysis": result["structured_output"]
    }
