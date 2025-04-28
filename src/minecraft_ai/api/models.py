from datetime import datetime
from typing import Any, ClassVar, List, Optional

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """Request model for chat messages."""

    message: str = Field(
        ...,
        description="The user's message to the AI agent.",
        min_length=1,
        examples=["Tell me about Pydantic", "How can I use PydanticAI?"],
    )

    @classmethod
    @field_validator("message")
    def message_not_empty(cls, v: str) -> str:
        """Validate that the message is not empty."""
        if not v.strip():
            raise ValueError("Message cannot be empty or consist only of whitespace")
        return v


class ChatResponse(BaseModel):
    """Response model for the AI agent's reply."""

    reply: str = Field(
        ...,
        description="The AI agent's response.",
        examples=["Pydantic is a data validation and settings management library..."],
    )

    model_config: ClassVar[dict[str, Any]] = {
        "json_schema_extra": {
            "example": {"reply": "Pydantic is a Python library for data validation and settings management."}
        }
    }


class ErrorResponse(BaseModel):
    """Model for error responses."""

    detail: str = Field(..., description="Error message details")
    status_code: int = Field(..., description="HTTP status code")


# --- Chat Endpoint Models ---


class NewChatRequest(BaseModel):
    """Request model for creating a new conversation."""

    topic: Optional[str] = Field(default=None, description="Optional topic or title for the conversation.")
    player_uuid: Optional[str] = Field(default=None, description="Minecraft player UUID.")
    player_username: Optional[str] = Field(default=None, description="Minecraft player username.")


class ConversationInfo(BaseModel):
    """Metadata for a conversation."""

    id: int
    topic: Optional[str] = None
    created_at: datetime
    player_uuid: Optional[str] = None
    player_username: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response model for listing conversations accessible to the user."""

    conversations: List[ConversationInfo]


class NewMessageRequest(BaseModel):
    """Request model for adding a new message to a conversation."""

    message: str = Field(..., description="The user's message to the AI assistant.")

    @classmethod
    @field_validator("message")
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty or consist only of whitespace")
        return v


class NewMessageResponse(BaseModel):
    """Response model for the AI agent's reply to a conversation message."""

    reply: str = Field(..., description="The AI agent's response.")
