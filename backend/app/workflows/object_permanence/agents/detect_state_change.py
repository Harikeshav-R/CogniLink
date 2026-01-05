import json

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from pydantic import BaseModel

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import ObjectPermanenceState


class StateChange(BaseModel):
    state_changed: bool


async def detect_state_change(state: ObjectPermanenceState) -> dict:
    if not state.current_analysis:
        logger.warning("No current analysis to check for state change.")
        return {"is_state_changed": False}

    if not state.last_saved_analysis:
        logger.debug("No last saved analysis found. This is the first run.")
        return {"is_state_changed": True}

    logger.debug("Initializing chat model for state change detection...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Chat model initialized.")

    logger.debug("Creating agent for state change detection...")
    agent = create_agent(
        model=model,
        response_format=StateChange,
        system_prompt=SystemMessage(
            content=Prompts.STATE_CHANGE_AGENT
        ),
    )
    logger.debug("Agent created.")

    previous_state_json = json.dumps([obj.model_dump() for obj in state.last_saved_analysis], indent=2)
    current_state_json = json.dumps([obj.model_dump() for obj in state.current_analysis], indent=2)

    result = await agent.ainvoke(
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Here are the two states to compare:"
                },
                {
                    "type": "text",
                    "text": f"previous_state: {previous_state_json}"
                },
                {
                    "type": "text",
                    "text": f"current_state: {current_state_json}"
                }
            ]
        )
    )
    logger.debug("Agent invocation complete.")

    state_change: StateChange = result["structured_response"]
    logger.debug(f"State change detected: {state_change.state_changed}")

    return {"is_state_changed": state_change.state_changed}
