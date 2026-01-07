from pydantic import BaseModel, Field


class GenerateAnswerOutput(BaseModel):
    answer: str = Field(..., description="The generated answer to the user's query.")
    object_was_found: bool = Field(..., description="Whether the requested object was found.")


class DbQueryOutput(BaseModel):
    object_name: str = Field(..., description="Name of the object (e.g., 'Black Car Keys').")
    description: str = Field(..., description="Natural language description of the object.")
    timestamp: str = Field(..., description="The timestamp of the log entry.")


class ObjectPermanenceWorkflowState(BaseModel):
    # Input
    query: str = Field(..., description="The user's query.")

    # Internal
    matching_entries: list[DbQueryOutput] = Field(default_factory=list,
                                                  description="The results of the database query for the given query.")

    # Output
    response: str = Field(default="", description="The final response to the user.")
