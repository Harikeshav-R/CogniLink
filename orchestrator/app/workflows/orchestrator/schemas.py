from typing import Literal

from pydantic import BaseModel, Field


class SelectedWorkflow(BaseModel):
    workflow: Literal["object_permanence", "face_recognition"] = Field(...,
                                                                       description="The name of the selected workflow to execute.")


class OrchestratorWorkflowState(BaseModel):
    # Input
    query: str = Field(..., description="The user's query.")

    # Internal
    selected_workflow: SelectedWorkflow = Field(..., description="The selected workflow to execute.")

    # Output
    response: str = Field(..., description="The final response to the user.")
