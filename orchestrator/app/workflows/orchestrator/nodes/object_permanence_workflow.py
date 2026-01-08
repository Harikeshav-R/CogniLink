from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState
from app.workflows.object_permanence.workflow import create_compiled_state_graph
from app.workflows.orchestrator.schemas import OrchestratorWorkflowState


async def object_permanence_workflow(state: OrchestratorWorkflowState) -> dict:
    """
    Asynchronous function that executes the object permanence workflow.

    This function utilizes a compiled state graph to process the given
    workflow state and manages its transitions through various states
    until the final result is computed. The initial state is constructed
    based on the provided workflow state, and the final state is validated
    using its model before being returned as part of a dictionary.

    :param state: The initial orchestrator workflow state that serves as
        input for the workflow execution.
    :type state: OrchestratorWorkflowState

    :return: A dictionary containing the response from the final validated
        object permanence workflow state.
    :rtype: dict
    """
    workflow = create_compiled_state_graph()
    initial_state = ObjectPermanenceWorkflowState(query=state.query)
    final_state: ObjectPermanenceWorkflowState = await workflow.ainvoke(initial_state)
    final_state = ObjectPermanenceWorkflowState.model_validate(final_state)

    return {
        "response": final_state.response
    }
