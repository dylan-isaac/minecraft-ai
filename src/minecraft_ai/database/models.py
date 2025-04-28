from datetime import datetime
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


class Conversation(SQLModel, table=True):
    """Represents a persistent AI conversation."""

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_identifier: str = Field(index=True, description="User identifier (API key or player UUID)")
    player_uuid: Optional[str] = Field(default=None, index=True, description="Minecraft player UUID")
    player_username: Optional[str] = Field(default=None, index=True, description="Minecraft player username")
    topic: Optional[str] = Field(default=None, description="Optional topic or title for the conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ConversationMessage(SQLModel, table=True):
    """Represents a message in a conversation (user or assistant)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", nullable=False, index=True)
    role: str = Field(description="'user' or 'assistant'")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
