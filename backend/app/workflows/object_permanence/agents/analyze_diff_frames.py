import base64
from loguru import logger
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, TextContentBlock, ImageContentBlock

from app.core.config import Config
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import State, DiffAnalysis


def analyze_diff_frames(state: State) -> dict:
    """
    Analyzes the differences between two image frames provided in the state object.

    This function utilizes a chat-based model to perform a detailed comparison of
    the `previous_frame` and `current_frame` attributes within the `state`. It prepares
    the necessary input data, initializes the model and agent, and invokes the analysis
    agent to generate a diff analysis result. If either the `previous_frame` or
    `current_frame` is missing from the state, the function returns an empty dictionary.

    :param state: The state object containing `previous_frame` and `current_frame`
        attributes as image data. Must be of type State.
    :return: A dictionary containing the diff analysis result under the key
        `diff_analysis`. If the required frames are not available, returns an empty
        dictionary.
    :rtype: dict
    """
    logger.trace("Entering analyze_diff_frames function")
    if state.previous_frame is None or state.current_frame is None:
        logger.debug("Previous frame or current frame is None, returning empty dict")
        return {}

    logger.debug("Initializing chat model for diff frames analysis")
    model = init_chat_model(
        model=Config.GEMINI_VISION_MODEL,
        model_provider=Config.GEMINI_PROVIDER,
        api_key=Config.GEMINI_API_KEY
    )

    logger.debug("Creating agent for diff frames analysis")
    agent = create_agent(
        model=model,
        response_format=DiffAnalysis,
        system_prompt=SystemMessage(
            content=Prompts.ANALYZE_DIFF_FRAMES
        ),
    )

    logger.debug("Invoking agent for diff frames analysis")
    prev_image_data = base64.b64encode(state.previous_frame.tobytes()).decode("utf-8")
    curr_image_data = base64.b64encode(state.current_frame.tobytes()).decode("utf-8")
    logger.debug(f"Previous image data length: {len(prev_image_data)}")
    logger.debug(f"Current image data length: {len(curr_image_data)}")

    result = agent.invoke(
        HumanMessage(
            content_blocks=[
                TextContentBlock(
                    type="text",
                    text=Prompts.ANALYZE_DIFF_FRAMES
                ),
                ImageContentBlock(
                    type="image",
                    url=f"data:image/png;base64,{prev_image_data}"
                ),
                ImageContentBlock(
                    type="image",
                    url=f"data:image/png;base64,{curr_image_data}"
                ),
            ]
        )
    )
    logger.debug(f"Agent invocation result: {result}")

    logger.trace("Exiting analyze_diff_frames function")
    return {
        "diff_analysis": result["structured_output"]
    }
