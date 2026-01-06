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
    if not state.current_frame_b64:
        return {}

    model = init_pollinations_chat_model(
        Config.POLLINATIONS_VISION_MODEL,
        Config.POLLINATIONS_API_KEY
    )

    # model = init_google_genai_chat_model(
    #     Config.GEMINI_FAST_MODEL,
    #     Config.GEMINI_API_KEY
    # )

    agent = create_agent(
        model=model,
        response_format=FrameAnalysis,
        system_prompt=SystemMessage(
            content=Prompts.ANALYZE_FRAME
        ),
    )

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
    response: FrameAnalysis = response["structured_response"]

    logger.info(f"Detected Room: {response.scene.room_name}")
    logger.info(f"Detected {len(response.objects)} objects.")

    return {"current_analysis": response}
