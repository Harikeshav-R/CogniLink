from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.shared.frame_broadcaster import frame_broadcaster
from app.workflows.object_permanence.agents.analyze_frames import analyze_frame
from app.workflows.object_permanence.agents.detect_state_change import detect_state_change
from app.workflows.object_permanence.agents.format_and_save_state import format_and_save_state
from app.workflows.object_permanence.state import ObjectPermanenceState


def should_save_analysis(state: ObjectPermanenceState) -> str:
    """
    Determines whether the analysis should be saved based on whether a state change was detected.

    :param state: The current state of the workflow.
    :return: "format_and_save_state" if a change was detected, otherwise END.
    """
    logger.debug(f"Checking for state change. Detected: {state.is_state_changed}")
    if state.is_state_changed:
        return "format_and_save_state"
    else:
        return END


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
    workflow.add_node("detect_state_change", detect_state_change)
    workflow.add_node("format_and_save_state", format_and_save_state)

    logger.debug("Setting entry point to 'retrieve_frame'")
    workflow.set_entry_point("retrieve_frame")

    logger.debug("Adding edges to the graph")
    workflow.add_edge("retrieve_frame", "analyze_frame")
    workflow.add_edge("analyze_frame", "detect_state_change")
    workflow.add_conditional_edges(
        "detect_state_change",
        should_save_analysis,
        {
            "format_and_save_state": "format_and_save_state",
            END: END
        }
    )
    workflow.add_edge("format_and_save_state", END)

    logger.debug("Compiling the state graph")
    compiled_graph = workflow.compile()
    logger.trace("Exiting create_compiled_state_graph function")
    return compiled_graph
