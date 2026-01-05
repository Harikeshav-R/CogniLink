import base64
import io

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
    Asynchronously analyzes the given frame using a pre-initialized agent, leveraging a
    chat model for object permanence analysis. The function prepares the input frame,
    configures the agent, and invokes it to perform the required analysis. It extracts
    the results in a structured format upon completion.

    :param state: The state object containing the frame to analyze. The frame is expected
        to be in a compatible format for encoding and transmission.
    :type state: ObjectPermanenceState

    :return: A dictionary containing the results of the object permanence analysis.
    :rtype: dict
    """
    logger.trace("Entering analyze_frames function")

    if not state.frame:
        logger.warning("No frame provided to analyze.")
        return {}

    logger.debug(f"Analyzing the frame.")

    logger.debug("Initializing chat model for frame analysis...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Chat model initialized.")

    logger.debug("Creating agent for frame analysis...")
    agent = create_agent(
        model=model,
        response_format=RootModel[list[ObjectPermanenceObject]],
        system_prompt=SystemMessage(
            content=Prompts.FRAME_ANALYSIS_AGENT
        ),
    )
    logger.debug("Agent created.")

    logger.trace("Encoding frame to base64...")
    image_bytes = io.BytesIO()
    state.frame.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    image_data = base64.b64encode(image_bytes.getvalue()).decode("utf-8")

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
    logger.debug("Agent invocation complete.")

    analysis: list[ObjectPermanenceObject] = result["structured_response"]
    logger.debug(f"Analysis result: {analysis.model_dump_json(indent=2)}")

    logger.trace("Exiting analyze_frames function")
    return {
        "current_analysis": analysis
    }
