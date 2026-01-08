from app.workflows.orchestrator.schemas import OrchestratorWorkflowState


async def face_recognition_workflow(state: OrchestratorWorkflowState) -> dict:
    return {"response": "Hello, World!"}
