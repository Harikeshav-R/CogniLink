from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from app.core.config import Config
from app.core.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import State, FilteredResults


async def filter_results(state: State) -> dict:
    """
    Filters results using static and differential analysis data from the given state. This
    function employs a chat model-based agent to generate filtered outputs based on the
    provided inputs. If either static or diff analysis is absent, an empty dictionary is
    returned.

    :param state: The state containing static analysis and diff analysis data used for
        filtering. Must be an instance of the `State` class with appropriate attributes.

    :return: A dictionary containing filtered results under the key "filtered_results"
        generated through the agent. If the analysis data in the state is not available,
        an empty dictionary is returned.
    :rtype: dict
    """
    logger.trace("Entering filter_results function")
    if state.static_analysis is None or state.diff_analysis is None:
        logger.debug("Static analysis or diff analysis is None, returning empty dict")
        return {}

    logger.debug(f"Static analysis input: {state.static_analysis.model_dump_json(indent=2)}")
    logger.debug(f"Diff analysis input: {state.diff_analysis.model_dump_json(indent=2)}")

    # Filter out low-confidence objects and events before sending to the agent
    if state.static_analysis:
        logger.debug(f"Filtering {len(state.static_analysis.objects)} objects.")
        state.static_analysis.objects = [
            obj for obj in state.static_analysis.objects if obj.confidence != "low"
        ]
        logger.debug(f"Found {len(state.static_analysis.objects)} objects after filtering.")
    if state.diff_analysis:
        logger.debug(f"Filtering {len(state.diff_analysis.events)} events.")
        state.diff_analysis.events = [
            event for event in state.diff_analysis.events if event.confidence != "low"
        ]
        logger.debug(f"Found {len(state.diff_analysis.events)} events after filtering.")

    logger.debug("Initializing chat model for filtering...")

    # model = init_google_genai_chat_model(
    #     Config.GEMINI_VISION_MODEL,
    #     Config.GEMINI_API_KEY
    # )

    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Chat model initialized.")

    logger.debug("Creating agent for filtering results...")
    agent = create_agent(
        model=model,
        response_format=FilteredResults,
        system_prompt=SystemMessage(
            content=Prompts.FILTER_RESULTS
        ),
    )
    logger.debug("Agent created.")

    logger.debug("Invoking agent to filter results...")
    result = await agent.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": Prompts.FILTER_RESULTS
                        },
                        {
                            "type": "text",
                            "text": str(state.static_analysis.model_dump())
                        },
                        {
                            "type": "text",
                            "text": str(state.diff_analysis.model_dump())
                        }
                    ]
                )
            ]
        }
    )
    logger.debug("Agent invocation complete.")
    logger.debug(f"Filtered results: {result['structured_response'].model_dump_json(indent=2)}")

    logger.trace("Exiting filter_results function")
    return {
        "filtered_results": result["structured_response"]
    }
