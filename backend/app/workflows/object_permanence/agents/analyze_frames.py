import base64
import io
import json

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from pydantic import RootModel

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import ObjectPermanenceState, ObjectPermanenceObject


async def analyze_frame(state: ObjectPermanenceState) -> dict:
    """
    Analyzes a single video frame to detect and identify objects, their properties,
    and their spatial relationships. It uses a vision-capable chat model to perform
    the analysis.

    :param state: The current state of the workflow, containing the frame to be analyzed.
    :type state: ObjectPermanenceState
    :return: A dictionary containing the results of the analysis under the key 'current_analysis'.
    :rtype: dict
    """
    logger.trace("Entering 'analyze_frame' node.")

    if not state.frame:
        logger.warning("No frame provided in the state to analyze. Skipping analysis.")
        return {"current_analysis": []}

    logger.info(f"Beginning frame analysis for a frame of size {state.frame.size}.")

    logger.debug("Initializing vision chat model for frame analysis...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Vision chat model initialized.")

    logger.debug("Creating vision agent for frame analysis...")
    agent = create_agent(
        model=model,
        response_format=RootModel[list[ObjectPermanenceObject]],
        system_prompt=SystemMessage(
            content=Prompts.FRAME_ANALYSIS_AGENT
        ),
    )
    logger.debug("Vision agent created.")

    logger.debug("Encoding frame to base64 for API transmission...")
    image_bytes = io.BytesIO()
    state.frame.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    image_data = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
    logger.trace(f"Frame encoded to base64 string of length {len(image_data)}.")

    logger.info("Invoking vision agent to analyze frame...")
    result = await agent.ainvoke(
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": Prompts.FRAME_ANALYSIS_AGENT
                },
                {
                    "type": "text",
                    "text": "Here is your frame to analyze:"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}"
                    }
                }
            ]
        )
    )
    logger.info("Agent invocation complete.")

    analysis: list[ObjectPermanenceObject] = result["structured_response"]
    analysis_json = json.dumps([obj.model_dump() for obj in analysis], indent=2)
    logger.debug(f"Agent returned {len(analysis)} objects from analysis.")
    logger.trace(f"Full analysis result (JSON):\n{analysis_json}")

    logger.trace("Exiting 'analyze_frame' node.")
    return {
        "current_analysis": analysis
    }
