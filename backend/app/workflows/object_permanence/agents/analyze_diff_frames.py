import base64

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, TextContentBlock, ImageContentBlock

from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import State, DiffAnalysis


def analyze_diff_frames(state: State):
    if state.previous_frame is None or state.current_frame is None:
        return {}

    model = init_chat_model(
        model="gemma-3-27b-it",
        model_provider="google_genai"
    )
    agent = create_agent(
        model=model,
        response_format=ProviderStrategy(DiffAnalysis),
        system_prompt=SystemMessage(
            content=Prompts.ANALYZE_DIFF_FRAMES
        ),
    )

    result = agent.invoke(
        HumanMessage(
            content_blocks=[
                TextContentBlock(
                    type="text",
                    text=Prompts.ANALYZE_DIFF_FRAMES
                ),
                ImageContentBlock(
                    type="image",
                    url=f"data:image/png;base64,{base64.b64encode(state.previous_frame.tobytes()).decode("utf-8")}"
                ),
                ImageContentBlock(
                    type="image",
                    url=f"data:image/png;base64,{base64.b64encode(state.current_frame.tobytes()).decode("utf-8")}"
                ),
            ]
        )
    )

    return {
        "_diff_analysis": result["structured_output"]
    }
