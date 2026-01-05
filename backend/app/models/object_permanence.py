from typing import Optional, Literal

from loguru import logger
from pgvector.sqlalchemy import Vector
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import SQLModel, Field, Column


class ObjectPermanence(SQLModel, table=True):
    """
    Represents an object's state at a specific point in time, stored in the database.
    This model is used to track objects, their descriptions, locations, and confidence levels,
    along with an embedding for semantic search.
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="The primary key of the table.")
    timestamp: float = Field(index=True, description="The timestamp of the log entry.")

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
        default=[], sa_column=Column(ARRAY(String)),
        description="A list of precise relation to landmarks (e.g., 'on the white marble counter', 'next to the red mug', 'under the table lamp')."
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="The confidence level of the object detection (high, medium, low)."
    )

    formatted_description: str = Field(
        description="A formatted description of the object that contains the metadata of the object: name, description, location, and landmarks, "
                    "in a way that makes it easily indexable during RAG vector searches."
    )
    embedding: list[float] = Field(sa_column=Column(Vector(3072)),
                                   description="The embedding of the formatted description of the object.")


logger.debug("SQLModel 'ObjectPermanence' defined.")