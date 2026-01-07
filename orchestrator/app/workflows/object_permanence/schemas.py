from pydantic import BaseModel, Field


class DbQueryOutput(BaseModel):
    object_name: str = Field(..., description="Name of the object (e.g., 'Black Car Keys').")
    description: str = Field(..., description="Natural language description of the object.")
    timestamp: str = Field(..., description="The timestamp of the log entry.")


class ObjectPermanenceWorkflowState(BaseModel):
    # Input
    query: str = Field(..., description="The user's query.")

    # Internal
    number_of_entries_to_query: int = Field(default=5, description="The number of entries to query from the database.")
    matching_entries: list[DbQueryOutput] = Field(default_factory=list,
                                                  description="The results of the database query for the given query.")
    found_matching_entries: bool = Field(default=False,
                                         description="Whether the query found any relevant results in the DB.")
    query_results_were_sufficient: bool = Field(default=False,
                                                description="Whether the query results from the database were sufficient.")

    # Output
    response: str = Field(default="", description="The final response to the user.")
