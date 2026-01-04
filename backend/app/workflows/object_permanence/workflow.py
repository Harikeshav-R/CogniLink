from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.workflows.object_permanence.agents.analyze_frames import analyze_frames
from app.workflows.object_permanence.agents.extract_frames import extract_frames
from app.workflows.object_permanence.agents.filter_results import filter_results
from app.workflows.object_permanence.agents.save_analysis import save_analysis
from app.workflows.object_permanence.state import State


def create_compiled_state_graph() -> CompiledStateGraph:
    """
    Creates and compiles a `StateGraph` representing the workflow for object permanence analysis.

    The function initializes a `StateGraph` and adds nodes and edges to represent various stages
    of the analysis process. It specifies an entry point, conditional logic for transitions
    between states, and the finish point of the graph. Finally, it compiles the graph into
    a `CompiledStateGraph` object.

    :raises WorkflowError: If the `StateGraph` cannot be compiled due to invalid definitions.
    :return: A compiled state graph containing the defined workflow for object permanence analysis
    :rtype: CompiledStateGraph
    """
    logger.trace("Entering create_compiled_state_graph function")
    logger.debug("Creating StateGraph for Object Permanence")
    workflow = StateGraph(State)

    logger.debug("Adding nodes to the graph")
    workflow.add_node("extract_frames", extract_frames)
    workflow.add_node("analyze_frames", analyze_frames)
    workflow.add_node("filter_results", filter_results)
    workflow.add_node("save_analysis", save_analysis)

    logger.debug("Setting entry point to 'extract_frames'")
    workflow.set_entry_point("extract_frames")

    logger.debug("Adding edge from 'extract_frames' to 'analyze_frames'")
    workflow.add_edge("extract_frames", "analyze_frames")

    logger.debug("Adding edge from 'analyze_frames' to 'filter_results'")
    workflow.add_edge("analyze_frames", "filter_results")

    logger.debug("Adding edge from 'filter_results' to 'save_analysis'")
    workflow.add_edge("filter_results", "save_analysis")

    logger.debug("Setting finish point to 'save_analysis'")
    workflow.set_finish_point("save_analysis")

    logger.debug("Compiling the state graph")
    compiled_graph = workflow.compile()
    logger.trace("Exiting create_compiled_state_graph function")
    return compiled_graph

