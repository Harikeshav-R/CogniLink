from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession


class DetectedObject(BaseModel):
    object_name: str = Field(..., description="Name of the object (e.g., 'Black Car Keys').")
    visual_description: str = Field(..., description="Visual details (e.g., 'Silver keys with blue fob').")
    location_coords: list[float] = Field(..., description="[x, y] normalized coordinates (0.0-1.0).")
    landmarks: list[str] = Field(..., description="Nearby fixed landmarks (e.g., 'next to the lamp').")
    confidence: float = Field(..., description="Detection confidence (0.0-1.0).")


class GlobalScene(BaseModel):
    room_name: str = Field(..., description="Inferred room name (e.g., 'Kitchen').")
    scene_summary: str = Field(..., description="Brief summary of the environment.")


class FrameAnalysis(BaseModel):
    scene: GlobalScene = Field(..., description="The global context of the frame.")
    objects: list[DetectedObject] = Field(description="list of objects detected.", default_factory=list)


# --- Model for Node 2 (Deduplication Logic) ---
class DeduplicationResult(BaseModel):
    unique_object_indices: list[int] = Field(
        description="list of indices from the 'current_objects' input that represent NEW or CHANGED items.",
        default_factory=list
    )
    reasoning: str = Field(..., description="Brief explanation of the decision.")


class ObjectDescription(BaseModel):
    object_index: int = Field(description="The original index of this object in the input list.")
    searchable_text: str = Field(description="The natural language description string.")


class DescriptionBatch(BaseModel):
    descriptions: list[ObjectDescription] = Field(description="List of descriptions for all provided objects.")


class ObjectPermanenceWorkflowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Inputs
    current_frame_b64: str = Field(..., description="Encoded image data in Base64 format.")
    previous_frame_objects: Optional[list[DetectedObject]] = Field(description="List of objects from previous frame.",
                                                                   default_factory=list)
    previous_room: Optional[str] = Field(description="Name of the previous room.", default=None)
    db_session: AsyncSession = Field(exclude=True)

    # Internal
    current_analysis: Optional[FrameAnalysis] = Field(description="Analysis of the current frame.", default=None)
    unique_objects: list[DetectedObject] = Field(description="List of unique objects detected in the current frame.",
                                                 default_factory=list)
    generated_descriptions: list[str] = Field(description="List of natural language descriptions for unique objects.",
                                              default_factory=list)

    # Output
    final_storage_status: Optional[str] = Field(description="Status of the final storage operation.", default=None)