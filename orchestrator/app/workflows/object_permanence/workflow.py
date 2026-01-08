from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.workflows.object_permanence.nodes.generate_answer import generate_answer
from app.workflows.object_permanence.nodes.retrieve_matching_objects import retrieve_matching_objects
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState


def create_compiled_state_graph() -> CompiledStateGraph:
    """
    Creates and compiles a state graph for processing an object permanence workflow.

    The function initializes a `StateGraph` instance using the
    `ObjectPermanenceWorkflowState` as the workflow state. It sets up the nodes
    and transitions within the graph, designating an entry point, finish point,
    and all relevant edges between nodes. Finally, it compiles the graph into a
    `CompiledStateGraph` object for subsequent use.

    :return: A compiled state graph object for the object permanence workflow.
    :rtype: CompiledStateGraph
    """
    workflow = StateGraph(ObjectPermanenceWorkflowState)

    logger.debug("Adding nodes to the graph")
    workflow.add_node("retrieve_matching_objects", retrieve_matching_objects)
    workflow.add_node("generate_answer", generate_answer)

    logger.debug("Setting entry point to 'retrieve_matching_objects'")
    workflow.set_entry_point("retrieve_matching_objects")

    logger.debug("Adding edges to the graph")
    workflow.add_edge("retrieve_matching_objects", "generate_answer")

    logger.debug("Setting finish point to 'generate_answer'")
    workflow.set_finish_point("generate_answer")

    logger.debug("Compiling the state graph")
    compiled_graph = workflow.compile()
    logger.trace("Exiting create_compiled_state_graph function")
    return compiled_graph
