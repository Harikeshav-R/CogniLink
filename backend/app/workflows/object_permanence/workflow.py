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
    Determines the next step in the workflow based on whether a state change was detected.

    :param state: The current state of the workflow, containing the `is_state_changed` flag.
    :return: "format_and_save_state" if a change was detected, otherwise END to terminate the flow.
    """
    logger.debug("Evaluating conditional edge: 'should_save_analysis'")
    if state.is_state_changed:
        logger.info("State change detected. Proceeding to 'format_and_save_state' node.")
        return "format_and_save_state"
    else:
        logger.info("No state change detected. Ending workflow for this frame.")
        return END


def create_compiled_state_graph() -> CompiledStateGraph:
    """
    Creates and compiles the state graph for the object permanence workflow.

    This function defines the structure of the workflow, connecting different processing
    steps (nodes) together based on a set of rules (edges). The resulting compiled
    graph is a callable object that executes the defined workflow.

    :return: A compiled `CompiledStateGraph` instance ready for execution.
    """
    logger.info("Creating StateGraph for Object Permanence workflow.")
    workflow = StateGraph(ObjectPermanenceState)

    logger.debug("Adding node: 'retrieve_frame'")
    workflow.add_node("retrieve_frame",
                      lambda state: {"frame": frame_broadcaster.get_frame(state.subscriber_id)})

    logger.debug("Adding node: 'analyze_frame'")
    workflow.add_node("analyze_frame", analyze_frame)

    logger.debug("Adding node: 'detect_state_change'")
    workflow.add_node("detect_state_change", detect_state_change)

    logger.debug("Adding node: 'format_and_save_state'")
    workflow.add_node("format_and_save_state", format_and_save_state)

    logger.info("Defining graph structure (edges).")

    logger.debug("Setting entry point to 'retrieve_frame'.")
    workflow.set_entry_point("retrieve_frame")

    logger.debug("Adding edge from 'retrieve_frame' to 'analyze_frame'.")
    workflow.add_edge("retrieve_frame", "analyze_frame")

    logger.debug("Adding edge from 'analyze_frame' to 'detect_state_change'.")
    workflow.add_edge("analyze_frame", "detect_state_change")

    logger.debug("Adding conditional edge from 'detect_state_change' based on 'should_save_analysis'.")
    workflow.add_conditional_edges(
        "detect_state_change",
        should_save_analysis,
        {
            "format_and_save_state": "format_and_save_state",
            END: END
        }
    )

    logger.debug("Adding edge from 'format_and_save_state' to END.")
    workflow.add_edge("format_and_save_state", END)

    logger.info("Compiling the state graph...")
    compiled_graph = workflow.compile()
    logger.info("State graph compiled successfully.")
    logger.trace("Exiting create_compiled_state_graph function")
    return compiled_graph
