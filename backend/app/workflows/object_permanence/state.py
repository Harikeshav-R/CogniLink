from typing import Literal, Optional

from PIL.Image import Image
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel.ext.asyncio.session import AsyncSession


class ObjectPermanenceObject(BaseModel):
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

    formatted_description: Optional[str] = Field(
        description="A formatted description of the object that contains the metadata of the object: name, description, location, and landmarks, "
                    "in a way that makes it easily indexable during RAG vector searches."
    )


class ObjectPermanenceState(BaseModel, table=True):
    # Inputs
    subscriber_id: str = Field(..., description="The subscriber ID of the agent subscribing to the state updates.")
    frame: Optional[Image] = Field(default=None, description="The current frame to process.")
    last_saved_analysis: Optional[list[ObjectPermanenceObject]] = Field(
        default=None,
        description="Memory of the last saved state"
    )

    # Internal state
    db_session: AsyncSession
    current_analysis: Optional[list[ObjectPermanenceObject]] = Field(
        default=None,
        description="Analysis of the current frame"
    )
    is_state_changed: bool = Field(
        default=False,
        description="Flag indicating if a change was detected"
    )

    # Output
    save_status: bool = Field(
        default=False,
        description="Whether the analysis results have been saved to the database."
    )

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=True)
