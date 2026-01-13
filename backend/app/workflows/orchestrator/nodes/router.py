from loguru import logger
from app.workflows.orchestrator.schemas import OrchestratorWorkflowState


def router(state: OrchestratorWorkflowState) -> str:
    """
    Routes the workflow to the appropriate node based on the selected workflow.

    :param state: The current state of the orchestrator workflow.
    :type state: OrchestratorWorkflowState
    :return: The name of the workflow to execute.
    :rtype: str
    """
    logger.info("Routing to the selected workflow.")
    logger.debug(f"Current state: {state}")

    if state.selected_workflow:
        workflow_name = state.selected_workflow.workflow
        logger.success(f"Routing to '{workflow_name}' workflow.")
        return workflow_name
    else:
        logger.error("No workflow selected. Cannot route.")
        raise ValueError("The 'selected_workflow' attribute is not set in the workflow state.")