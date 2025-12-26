from typing import Optional, Literal

from PIL import Image
from pydantic import BaseModel, Field


class Object(BaseModel):
    object_name: str = Field(
        description="The name of the object. Specific name (e.g. 'Silver Car Keys', not just 'Keys')")
    category: str = Field(
        description="The category of the object: electronics | keys | wallet | eyewear | medication | stationery | other")
    status: str = Field(description="The status of the object: held | worn | resting")
    location_description: str = Field(
        description="Precise relation to landmarks (e.g., 'on the white marble counter, next to the red mug').")
    supporting_surface: str = Field(
        description="The specific item underneath (e.g., 'Kitchen Table', 'Sofa Cushion', 'Floor').")
    visual_details: str = Field(description="Distinguishing features (color, brand, condition).")
    confidence: str = Field(description="high | medium | low")


class StaticAnalysis(BaseModel):
    scene_description: str = Field(
        description="A brief 1-sentence summary of the context (e.g., 'A cluttered kitchen countertop with harsh lighting').")
    objects: list[Object] = Field(description="A list of detected objects.", default_factory=list)


class Event(BaseModel):
    event_type: str = Field(description="The type of event that occurred: placed | removed | moved")
    object_name: str = Field(description="The name of the object that was affected.")
    action_description: str = Field(
        description="Natural language summary of the action (e.g. 'The user placed their reading glasses on the nightstand').")
    location_context: str = Field(description="Where the interaction happened (e.g. 'The Nightstand').")
    confidence: str = Field(description="high | medium | low")


class DiffAnalysis(BaseModel):
    events: list[Event] = Field(description="A list of detected events.", default_factory=list)


class FilteredEntry(BaseModel):
    content: str = Field(description="The natural language description of the log entry.")
    object_name: str = Field(description="The name of the object to log.")
    log_type: Literal["state", "action"] = Field(description="The type of log entry: state | action")


class FilteredResults(BaseModel):
    entries: list[FilteredEntry] = Field(description="A list of filtered entries.", default_factory=list)


class State(BaseModel):
    # Inputs
    current_frame: Image.Image
    previous_frame: Optional[Image.Image] = None
    timestamp: float

    # Internal
    should_analyze: bool = False
    static_analysis: Optional[StaticAnalysis] = None
    diff_analysis: Optional[DiffAnalysis] = None
    filtered_results: Optional[FilteredResults] = None

    # Outputs
    save_status: bool
