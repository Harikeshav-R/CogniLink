from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field, Column


class ObjectPermanence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="The primary key of the table.")
    timestamp: float = Field(index=True, description="The timestamp of the log entry.")

    object_name: str = Field(..., description="Name of the object (e.g., 'Black Car Keys').")
    description: str = Field(..., description="Natural language description of the object.")
    embedding: Vector = Field(sa_column=Column(Vector(3072)),
                              description="The embedding of the natural language description of the object.")
