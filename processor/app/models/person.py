from datetime import date
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.models.user import User


class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="The primary key of the table.")
    name: str = Field(index=True, description="The name of the person.")
    date_of_birth: Optional[date] = Field(default=None, description="The date of birth of the person.")
    relation_to_user: str = Field(description="The relationship of the person to the user.")

    # Foreign Key to link to the User
    user_id: int = Field(foreign_key="user.id")

    # Relationship: Link back to the User object
    user: Optional[User] = Relationship(back_populates="related_people")
