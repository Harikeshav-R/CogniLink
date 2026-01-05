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
    """
    Pydantic model to represent the result of a state change detection.
    It contains a single boolean field indicating whether a significant
    state change was detected.
    """
    state_changed: bool


async def detect_state_change(state: ObjectPermanenceState) -> dict:
    """
    Compares the current frame's analysis with the last saved analysis to determine
    if a significant change has occurred. This is a key step in deciding whether
    to save the new state.
    """
    logger.trace("Entering 'detect_state_change' node.")

    if not state.current_analysis:
        logger.warning("No current analysis available to check for state change. Assuming no change.")
        return {"is_state_changed": False}

    if not state.last_saved_analysis:
        logger.info("No last saved analysis found. This is the first run, so assuming state has changed.")
        return {"is_state_changed": True}

    logger.info("Comparing current analysis with last saved analysis to detect state change.")

    logger.debug("Initializing chat model for state change detection...")
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("State change detection model initialized.")

    logger.debug("Creating agent for state change detection...")
    agent = create_agent(
        model=model,
        response_format=StateChange,
        system_prompt=SystemMessage(
            content=Prompts.STATE_CHANGE_AGENT
        ),
    )
    logger.debug("State change detection agent created.")

    previous_state_json = json.dumps([obj.model_dump() for obj in state.last_saved_analysis], indent=2)
    current_state_json = json.dumps([obj.model_dump() for obj in state.current_analysis], indent=2)

    logger.trace(f"Previous state for comparison:\n{previous_state_json}")
    logger.trace(f"Current state for comparison:\n{current_state_json}")

    logger.info("Invoking state change detection agent...")
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
    logger.info("Agent invocation complete.")

    state_change: StateChange = result["structured_response"]
    logger.info(f"Agent determined state change: {state_change.state_changed}")

    logger.trace("Exiting 'detect_state_change' node.")
    return {"is_state_changed": state_change.state_changed}
