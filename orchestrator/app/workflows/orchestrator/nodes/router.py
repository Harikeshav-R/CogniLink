from app.workflows.orchestrator.schemas import OrchestratorWorkflowState


def router(state: OrchestratorWorkflowState) -> str:
    return state.selected_workflow.workflow
