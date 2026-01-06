from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.workflows.object_permanence.nodes.analyze_frame import analyze_frame
from app.workflows.object_permanence.nodes.deduplicate_objects import deduplicate_objects
from app.workflows.object_permanence.nodes.generate_descriptions import generate_descriptions
from app.workflows.object_permanence.nodes.save_analysis import save_analysis
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState


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
    workflow = StateGraph(ObjectPermanenceWorkflowState)

    logger.debug("Adding nodes to the graph")
    workflow.add_node("analyze_frame", analyze_frame)
    workflow.add_node("deduplicate_objects", deduplicate_objects)
    workflow.add_node("generate_descriptions", generate_descriptions)
    workflow.add_node("save_analysis", save_analysis)

    logger.debug("Setting entry point to 'analyze_frame'")
    workflow.set_entry_point("analyze_frame")

    logger.debug("Adding edges to the graph")
    workflow.add_edge("analyze_frame", "deduplicate_objects")
    workflow.add_edge("deduplicate_objects", "generate_descriptions")
    workflow.add_edge("generate_descriptions", "save_analysis")

    logger.debug("Setting finish point to 'save_analysis'")
    workflow.set_finish_point("save_analysis")

    logger.debug("Compiling the state graph")
    compiled_graph = workflow.compile()
    logger.trace("Exiting create_compiled_state_graph function")
    return compiled_graph
