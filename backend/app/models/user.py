from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field, Column, Relationship

from app.models.person import Person


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="The primary key of the table.")
    first_name: str = Field(index=True, description="The first name of the user.")
    last_name: str = Field(index=True, description="The last name of the user.")
    face_embedding: Optional[Vector] = Field(
        sa_column=Column(Vector(4096)), description="The embedding of the user."
    )

    # Relationship: One user can have many related people
    related_people: list[Person] = Relationship(back_populates="user")
