from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, TextContentBlock
from loguru import logger

from app.core.config import Config
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import State, FilteredResults


def filter_results(state: State) -> dict:
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

    logger.debug("Initializing chat model")
    model = init_chat_model(
        model=Config.GEMINI_FAST_MODEL,
        model_provider=Config.GEMINI_PROVIDER,
        api_key=Config.GEMINI_API_KEY
    )

    logger.debug("Creating agent for filtering results")
    agent = create_agent(
        model=model,
        response_format=FilteredResults,
        system_prompt=SystemMessage(
            content=Prompts.FILTER_RESULTS
        ),
    )

    logger.debug("Invoking agent to filter results")
    result = agent.invoke(
        HumanMessage(
            content_blocks=[
                TextContentBlock(
                    type="text",
                    text=Prompts.FILTER_RESULTS
                ),
                TextContentBlock(
                    type="text",
                    text=str(state.static_analysis.model_dump())
                ),
                TextContentBlock(
                    type="text",
                    text=str(state.diff_analysis.model_dump())
                )
            ]
        )
    )
    logger.debug(f"Agent invocation result: {result}")

    logger.trace("Exiting filter_results function")
    return {
        "filtered_results": result["structured_output"]
    }
