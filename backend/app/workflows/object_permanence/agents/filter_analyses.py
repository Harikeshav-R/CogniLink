import json

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from pydantic import RootModel

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import ObjectPermanenceState, ObjectPermanenceAnalysis


async def filter_analyses(state: ObjectPermanenceState) -> dict:
    if len(state.past_analyses) < 10:
        return {"filtered_analyses": state.past_analyses}

    logger.debug("Initializing chat model for frame analysis...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Chat model initialized.")

    logger.debug("Creating agent for frame analysis...")
    agent = create_agent(
        model=model,
        response_format=RootModel[list[ObjectPermanenceAnalysis]],
        system_prompt=SystemMessage(
            content=Prompts.ANALYSES_FILTER_AGENT
        ),
    )
    logger.debug("Agent created.")

    result = await agent.ainvoke(
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": Prompts.ANALYSES_FILTER_AGENT
                },
                {
                    "type": "text",
                    "text": "Here is your list of analyses to filter:"
                },
                {
                    "type": "text",
                    "text": json.dumps([obj.model_dump() for obj in state.past_analyses], indent=2)
                }
            ]
        )
    )
    logger.debug("Agent invocation complete.")

    analysis: ObjectPermanenceAnalysis = result["structured_response"]
    logger.debug(f"Analysis result: {analysis.model_dump_json(indent=2)}")

    logger.trace("Exiting analyze_frames function")
    return {
        "analysis": analysis
    }
