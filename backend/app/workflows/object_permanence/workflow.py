from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.workflows.object_permanence.agents.analyze_frames import analyze_frame
from app.workflows.object_permanence.state import ObjectPermanenceState


def create_compiled_state_graph() -> CompiledStateGraph:
    """
    Creates and compiles a state graph for object permanence.

    This function initializes a StateGraph instance using the ObjectPermanenceState,
    adds necessary nodes to the graph, establishes its entry and finish points, and
    compiles the graph. The compiled state graph is then returned.

    :return: A compiled state graph instance configured for object permanence.
    :rtype: CompiledStateGraph
    """
    logger.trace("Entering create_compiled_state_graph function")
    logger.debug("Creating StateGraph for Object Permanence")
    workflow = StateGraph(ObjectPermanenceState)

    logger.debug("Adding nodes to the graph")
    workflow.add_node("analyze_frame", analyze_frame)

    logger.debug("Setting entry point to 'analyze_frame'")
    workflow.set_entry_point("analyze_frames")

    logger.debug("Setting finish point to 'analyze_frame'")
    workflow.set_finish_point("analyze_frames")

    logger.debug("Compiling the state graph")
    compiled_graph = workflow.compile()
    logger.trace("Exiting create_compiled_state_graph function")
    return compiled_graph
