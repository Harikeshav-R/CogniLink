from pydantic import BaseModel, Field


class OrchestratorWorkflowState(BaseModel):
    # Input
    query: str = Field(..., description="The user's query.")

    # Internal
    message_log: list = Field(default_factory=list,
                                   description="List of messages between user and different agents.")

    # Output
    response: str = Field(default="", description="The final response to the user.")
