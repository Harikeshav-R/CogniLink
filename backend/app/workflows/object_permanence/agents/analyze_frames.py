import base64
import io

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from app.core.config import Config
from app.core.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import State, VideoAnalysis


async def analyze_frames(state: State) -> dict:
    """
    Analyzes a sequence of frames to identify objects and events.

    This function uses a vision model to perform a detailed analysis of the frames
    provided in `state.frames`. It base64 encodes each frame and sends them to the
    model with a specialized prompt. The model is expected to return a structured
    response containing both a static analysis of the final scene and a differential
    analysis of events that occurred across the frames.

    The results are used to populate the `static_analysis` and `diff_analysis`
    fields in the workflow state.

    :param state: The current state of the workflow, containing the `frames` list.
    :type state: State
    :return: A dictionary containing the `static_analysis` and `diff_analysis` results.
    :rtype: dict
    """
    logger.trace("Entering analyze_frames function")
    if not state.frames:
        logger.warning("No frames provided to analyze.")
        return {}

    logger.debug(f"Analyzing {len(state.frames)} frames.")

    logger.debug("Initializing chat model for frame analysis...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Chat model initialized.")

    logger.debug("Creating agent for frame analysis...")
    agent = create_agent(
        model=model,
        response_format=VideoAnalysis,
        system_prompt=SystemMessage(
            content=Prompts.ANALYZE_FRAMES
        ),
    )
    logger.debug("Agent created.")

    content = [{"type": "text", "text": Prompts.ANALYZE_FRAMES}]
    for i, frame in enumerate(state.frames):
        logger.trace(f"Encoding frame {i + 1}/{len(state.frames)} to base64...")
        image_bytes = io.BytesIO()
        frame.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        image_data = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_data}"
            }
        })

    logger.debug(f"Invoking agent with {len(content)} content parts.")
    result = await agent.ainvoke({"messages": [HumanMessage(content=content)]})
    logger.debug("Agent invocation complete.")

    video_analysis: VideoAnalysis = result["structured_response"]
    logger.debug(f"Static analysis result: {video_analysis.static_analysis.model_dump_json(indent=2)}")
    logger.debug(f"Diff analysis result: {video_analysis.diff_analysis.model_dump_json(indent=2)}")

    logger.trace("Exiting analyze_frames function")
    return {
        "static_analysis": video_analysis.static_analysis,
        "diff_analysis": video_analysis.diff_analysis,
    }
