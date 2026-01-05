import json

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from pydantic import RootModel

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import ObjectPermanenceState, ObjectPermanenceObject


async def format_analyses(state: ObjectPermanenceState) -> dict:
    if not state.was_filtered:
        return {"formatted_analyses": []}

    logger.debug("Initializing chat model for analyses formatting...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Chat model initialized.")

    logger.debug("Creating agent for analyses formatting...")
    agent = create_agent(
        model=model,
        response_format=RootModel[list[ObjectPermanenceObject]],
        system_prompt=SystemMessage(
            content=Prompts.FORMAT_ANALYSES_AGENT
        ),
    )
    logger.debug("Agent created.")

    result = await agent.ainvoke(
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": Prompts.FORMAT_ANALYSES_AGENT
                },
                {
                    "type": "text",
                    "text": "Here is your list of analyses to format:"
                },
                {
                    "type": "text",
                    "text": json.dumps(
                        [obj.model_dump() for obj in state.filtered_analyses],
                        indent=2
                    )
                }
            ]
        )
    )
    logger.debug("Agent invocation complete.")

    formatted_analyses: list[ObjectPermanenceObject] = result["structured_response"]

    logger.trace("Exiting analyze_frames function")
    return {
        "formatted_analyses": formatted_analyses,
    }
