from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

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
    workflow = StateGraph(OrchestratorWorkflowState)

    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("object_permanence_workflow", object_permanence_workflow)
    workflow.add_node("face_recognition_workflow", face_recognition_workflow)

    workflow.set_entry_point("orchestrator")

    workflow.add_conditional_edges(
        "orchestrator",
        router,
        path_map
    )
    workflow.set_finish_point("object_permanence_workflow")
    workflow.set_finish_point("face_recognition_workflow")

    compiled_graph = workflow.compile()
    return compiled_graph
