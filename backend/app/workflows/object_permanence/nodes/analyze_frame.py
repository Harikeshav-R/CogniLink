from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from loguru import logger

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.schemas import FrameAnalysis, ObjectPermanenceWorkflowState


async def analyze_frame(state: ObjectPermanenceWorkflowState) -> dict:
    """
    Analyzes the current frame stored in the state using a machine learning model. This function
    utilizes an AI agent to process the encoded image from the frame and extracts structured
    information, including scene and objects detected within the image.

    :param state: The workflow state containing a base64-encoded representation of the current
        video frame to be analyzed.
    :type state: ObjectPermanenceWorkflowState

    :return: A dictionary containing the results of the analysis, including structured information
        about the detected scene and objects.
    :rtype: dict
    """
    logger.trace("Entering 'analyze_frame' node.")
    if not state.current_frame_b64:
        logger.warning("No frame data in state ('current_frame_b64' is empty). Skipping analysis.")
        return {}

    logger.debug(f"Frame has size: {len(state.current_frame_b64)} bytes. Initializing vision model...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.trace("Vision model initialized.")

    logger.debug("Creating analysis agent with structured output (FrameAnalysis).")
    agent = create_agent(
        model=model,
        response_format=FrameAnalysis,
        system_prompt=SystemMessage(
            content=Prompts.ANALYZE_FRAME
        ),
    )
    logger.trace("Analysis agent created.")

    logger.debug("Invoking agent to analyze frame...")
    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here is your frame to analyze:"},
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/png;base64,{state.current_frame_b64}"}},
                    ]
                }
            ]
        }
    )
    logger.trace(f"Agent invocation complete. Full response: {response}")

    structured_response: FrameAnalysis = response["structured_response"]
    logger.debug("Extracted structured response from agent output.")

    logger.info(
        f"Scene Analysis - Room: '{structured_response.scene.room_name}', Summary: '{structured_response.scene.scene_summary}'")
    logger.info(f"Object Detection - Found {len(structured_response.objects)} objects.")
    logger.trace(f"Detected objects: {structured_response.objects}")

    logger.trace("Exiting 'analyze_frame' node with new analysis.")
    return {"current_analysis": structured_response}
