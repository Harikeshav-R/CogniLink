from loguru import logger

from app.workflows.object_permanence.state import State


def gather_analyses(state: State) -> dict:
    """
    A simple node to gather results from parallel branches.
    This node doesn't perform any logic, but acts as a synchronization point in the graph.
    It logs the analyses received from the parallel branches.
    """
    logger.trace("Entering gather_analyses function")
    logger.debug("Gathering analyses from parallel branches")
    if state.static_analysis:
        logger.debug(f"Received static analysis: {state.static_analysis.model_dump_json(indent=2)}")
    else:
        logger.warning("Static analysis is missing")
    if state.diff_analysis:
        logger.debug(f"Received diff analysis: {state.diff_analysis.model_dump_json(indent=2)}")
    else:
        logger.warning("Diff analysis is missing")

    logger.trace("Exiting gather_analyses function")
    return {}
