from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState
from app.workflows.object_permanence.workflow import create_compiled_state_graph
from app.workflows.orchestrator.schemas import OrchestratorWorkflowState


async def object_permanence_workflow(state: OrchestratorWorkflowState) -> dict:
    workflow = create_compiled_state_graph()
    initial_state = ObjectPermanenceWorkflowState(query=state.query)
    final_state: ObjectPermanenceWorkflowState = await workflow.ainvoke(initial_state)
    final_state = ObjectPermanenceWorkflowState.model_validate(final_state)

    return {
        "response": final_state.response
    }
