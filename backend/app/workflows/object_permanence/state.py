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
    # Input
    subscriber_id: str = Field(..., description="The subscriber ID of the agent subscribing to the state updates.")
    frame: Optional[Image] = Field(default=None, description="The current frame to process.")
    past_analyses: list[ObjectPermanenceObject] = Field(
        description="A list of past object permanence frame analyses.",
        default_factory=list
    )

    # Internal
    db_session: AsyncSession
    analyses: list[ObjectPermanenceObject] = Field(
        description="The analysis results."
    )

    should_filter: bool = Field(
        default=False,
        description="Whether to filter the analyses."
    )
    filtered_analyses: list[ObjectPermanenceObject] = Field(
        description="A list of filtered object permanence frame analyses.",
        default_factory=list
    )

    # Output
    formatted_analyses: list[ObjectPermanenceObject] = Field(
        description="A list of formatted object permanence frame analyses.",
        default_factory=list
    )

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=True)
