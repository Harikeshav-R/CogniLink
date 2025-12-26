from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field, Column


class ObjectPermanence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="The primary key of the table.")
    content: str = Field(description="The natural language description of the log entry.")
    embedding: list[float] = Field(sa_column=Column(Vector(3072)), description="The embedding of the log entry.")
    timestamp: float = Field(index=True, description="The timestamp of the log entry.")
    object_name: str = Field(index=True, description="The name of the object to log.")
    log_type: str = Field(description="The type of log entry: state | action")
