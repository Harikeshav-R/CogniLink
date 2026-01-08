from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.workflows.orchestrator.nodes.face_recognition_workflow import face_recognition_workflow
from app.workflows.orchestrator.nodes.object_permanence_workflow import object_permanence_workflow
from app.workflows.orchestrator.nodes.orchestrator import orchestrator
from app.workflows.orchestrator.nodes.router import router
from app.workflows.orchestrator.schemas import OrchestratorWorkflowState

path_map = {
    "object_permanence": "object_permanence_workflow",
    "face_recognition": "face_recognition_workflow"
}


def create_compiled_state_graph() -> CompiledStateGraph:
    """
    Creates and compiles a state graph for a workflow system.

    This function initializes a `StateGraph` using the provided
    `OrchestratorWorkflowState` as the base. It adds multiple nodes to the
    graph, defines the entry point, sets up conditional edges using a
    router and path mapping, and sets the finish points for specific states.
    Finally, the state graph is compiled and returned as a `CompiledStateGraph`.

    :return: A fully compiled `CompiledStateGraph` object ready for execution
    :rtype: CompiledStateGraph
    """
    logger.info("Creating compiled state graph for the orchestrator.")
    workflow = StateGraph(OrchestratorWorkflowState)
    logger.trace("StateGraph initialized with OrchestratorWorkflowState.")

    logger.debug("Adding nodes to the graph.")
    workflow.add_node("orchestrator", orchestrator)
    logger.trace("Added node: 'orchestrator'")
    workflow.add_node("object_permanence_workflow", object_permanence_workflow)
    logger.trace("Added node: 'object_permanence_workflow'")
    workflow.add_node("face_recognition_workflow", face_recognition_workflow)
    logger.trace("Added node: 'face_recognition_workflow'")
    logger.debug("All nodes added.")

    logger.debug("Setting entry point to 'orchestrator'.")
    workflow.set_entry_point("orchestrator")
    logger.trace("Entry point set.")

    logger.debug("Adding conditional edges from 'orchestrator' using router.")
    workflow.add_conditional_edges(
        "orchestrator",
        router,
        path_map
    )
    logger.trace(f"Conditional edges added with path map: {path_map}")

    logger.debug("Setting finish points.")
    workflow.set_finish_point("object_permanence_workflow")
    logger.trace("Finish point set for 'object_permanence_workflow'.")
    workflow.set_finish_point("face_recognition_workflow")
    logger.trace("Finish point set for 'face_recognition_workflow'.")
    logger.debug("All finish points set.")

    logger.info("Compiling the state graph.")
    compiled_graph = workflow.compile()
    logger.success("State graph compiled successfully.")
    logger.trace(f"Returning compiled graph: {compiled_graph}")
    return compiled_graph

