from typing import Literal, Optional

from PIL.Image import Image
from pydantic import BaseModel, ConfigDict, Field


class ObjectPermanenceStateObject(BaseModel):
    name: str = Field(
        ...,
        description="The name of the object (e.g., 'mug','backpack', 'keys', 'wallet', 'headphones')."
    )
    description: str = Field(
        ...,
        description="A concise but detailed description of the object using adjective to describe the object "
                    "(e.g., 'small, red mug', 'old, green backpack', 'black toyota corolla keys', 'brown leather wallet with cards in it', 'pink bose quietcomfort headphones')."
    )
    location: str = Field(
        ...,
        description="The description of the location of the object (e.g., 'on the table', 'in the kitchen', 'in the living room')."
    )
    landmarks: list[str] = Field(
        description="A list of precise relation to landmarks (e.g., 'on the white marble counter', 'next to the red mug', 'under the table lamp').",
        default_factory=list
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="The confidence level of the object detection (high, medium, low)."
    )


class ObjectPermanenceAnalysis(BaseModel):
    scene: str = Field(
        ...,
        description="A concise description of the scene (e.g., 'A cluttered kitchen countertop with harsh lighting, with a few personal items on the dining table in the kitchen')."
    )
    objects: list[ObjectPermanenceStateObject] = Field(
        description="A list of detected objects in the scene.",
        default_factory=list
    )


class ObjectPermanenceState(BaseModel, table=True):
    # Input
    subscriber_id: str = Field(..., description="The subscriber ID of the agent subscribing to the state updates.")

    frame: Image = Field(..., description="The current frame to process.")

    # Output
    analysis: Optional[ObjectPermanenceAnalysis] = Field(
        description="The analysis results."
    )

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=True)
