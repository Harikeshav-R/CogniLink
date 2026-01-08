from loguru import logger

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
    logger.info("Executing object permanence workflow.")
    logger.debug(f"Current orchestrator state: {state}")

    logger.trace("Creating compiled state graph for object permanence.")
    workflow = create_compiled_state_graph()
    logger.trace("State graph created.")

    logger.debug(f"Initializing object permanence workflow with query: '{state.query}'")
    initial_state = ObjectPermanenceWorkflowState(query=state.query)
    logger.trace(f"Initial state for sub-workflow: {initial_state}")

    logger.debug("Invoking the object permanence workflow.")
    final_state: ObjectPermanenceWorkflowState = await workflow.ainvoke(initial_state)
    logger.debug("Object permanence workflow invocation complete.")
    logger.trace(f"Final state from sub-workflow: {final_state}")

    logger.trace("Validating final state model.")
    final_state = ObjectPermanenceWorkflowState.model_validate(final_state)
    logger.trace("Final state validated.")

    response = {"response": final_state.response}
    logger.success("Object permanence workflow executed successfully.")
    logger.trace(f"Returning response: {response}")
    return response

