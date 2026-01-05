from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.shared.frame_broadcaster import frame_broadcaster
from app.workflows.object_permanence.agents.analyze_frames import analyze_frame
from app.workflows.object_permanence.agents.filter_analyses import filter_analyses
from app.workflows.object_permanence.agents.format_analyses import format_analyses
from app.workflows.object_permanence.agents.save_analyses import save_analysis
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
    workflow.add_node("retrieve_frame",
                      lambda state: {"frame": frame_broadcaster.get_frame(state.subscriber_id)})
    workflow.add_node("analyze_frame", analyze_frame)
    workflow.add_node("filter_analyses", filter_analyses)
    workflow.add_node("format_analyses", format_analyses)
    workflow.add_node("save_analysis", save_analysis)

    logger.debug("Setting entry point to 'retrieve_frame'")
    workflow.set_entry_point("retrieve_frame")

    logger.debug("Adding edges to the graph")
    workflow.add_edge("retrieve_frame", "analyze_frame")
    workflow.add_edge("analyze_frame", "filter_analyses")
    workflow.add_edge("filter_analyses", "format_analyses")
    workflow.add_edge("format_analyses", "save_analysis")

    logger.debug("Setting finish point to 'save_analysis'")
    workflow.set_finish_point("save_analysis")

    logger.debug("Compiling the state graph")
    compiled_graph = workflow.compile()
    logger.trace("Exiting create_compiled_state_graph function")
    return compiled_graph
