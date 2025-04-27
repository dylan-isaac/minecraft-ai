from typing import Optional

from sqlmodel import Field, SQLModel


class SavedLocation(SQLModel, table=True):  # type: ignore
    """Represents a saved location in the Minecraft world."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    x: int
    y: int
    z: int
    dimension: str = Field(default="overworld")  # e.g., overworld, nether, end
    description: Optional[str] = Field(default=None)

    # TODO: Add created_at, updated_at timestamps if needed
    # TODO: Consider adding a user identifier if multiple users are expected
