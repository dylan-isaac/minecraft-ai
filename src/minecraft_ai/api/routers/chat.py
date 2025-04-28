import logging
import time
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic_ai.messages import ModelMessage
from sqlmodel import Session, select
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from ...agents import ai_agent  # Import agent from the new agents module
from ...database.database import get_session
from ...database.models import Conversation, ConversationMessage
from ..models import (
    ChatResponse,
    ConversationInfo,
    ConversationListResponse,
    NewChatRequest,
    NewMessageRequest,
    NewMessageResponse,
)

# TODO: Refactor agent initialization to a shared location
from ..security import verify_api_key  # Import from new security module

logger = logging.getLogger(__name__)

# --- Simple In-Memory Rate Limiter ---
RATE_LIMIT = 10  # requests
RATE_PERIOD = 60  # seconds
_rate_limit_store = {}


def rate_limiter(request: Request, api_key: str = Depends(verify_api_key)):
    now = int(time.time())
    key = f"{api_key}:{now // RATE_PERIOD}"
    count = _rate_limit_store.get(key, 0)
    if count >= RATE_LIMIT:
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {RATE_LIMIT} requests per {RATE_PERIOD} seconds.",
        )
    _rate_limit_store[key] = count + 1


router = APIRouter(
    prefix="/chats",
    tags=["Conversation Management"],
    dependencies=[Depends(verify_api_key), Depends(rate_limiter)],  # Apply API key auth and rate limiting to all routes
)


@router.post("", response_model=ConversationInfo, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: NewChatRequest,
    db: Session = Depends(get_session),
    api_key: str = Depends(verify_api_key),  # Inject validated API key
) -> ConversationInfo:
    """Creates a new conversation.

    Uses the authenticated user's identifier implicitly (from API key).
    """
    # Use the validated API key as the owner identifier
    owner_identifier = api_key

    conversation = Conversation(
        owner_identifier=owner_identifier,
        topic=request.topic,
        player_uuid=request.player_uuid,
        player_username=request.player_username,
        created_at=datetime.utcnow(),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    logger.info(f"Created new conversation ID {conversation.id} for owner {owner_identifier}")
    return ConversationInfo(
        id=conversation.id,
        topic=conversation.topic,
        created_at=conversation.created_at,
        player_uuid=conversation.player_uuid,
        player_username=conversation.player_username,
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    db: Session = Depends(get_session),
    api_key: str = Depends(verify_api_key),  # Inject validated API key
    player_uuid: str = None,
    player_username: str = None,
) -> ConversationListResponse:
    """
    Lists conversations accessible to the implicit owner (API key),
    with optional filtering by player UUID or username.
    """
    # Filter by the validated API key
    owner_identifier = api_key

    statement = select(Conversation).where(Conversation.owner_identifier == owner_identifier)
    if player_uuid:
        statement = statement.where(Conversation.player_uuid == player_uuid)
    if player_username:
        statement = statement.where(Conversation.player_username == player_username)
    conversations = db.exec(statement).all()
    logger.debug(
        f"Found {len(conversations)} conversations for owner {owner_identifier} "
        f"(uuid={player_uuid}, username={player_username})"
    )

    return ConversationListResponse(
        conversations=[
            ConversationInfo(
                id=c.id,
                topic=c.topic,
                created_at=c.created_at,
                player_uuid=c.player_uuid,
                player_username=c.player_username,
            )
            for c in conversations
        ]
    )


@router.post("/{conversation_id}/messages", response_model=NewMessageResponse)
async def add_message_to_conversation(
    conversation_id: int,
    request: NewMessageRequest,
    db: Session = Depends(get_session),
    api_key: str = Depends(verify_api_key),  # Inject validated API key
) -> NewMessageResponse:
    """Adds a user message to a conversation and gets the AI's reply.

    Verifies conversation ownership against the provided API key.
    Retrieves history, interacts with the PydanticAI agent, and stores both messages.
    """
    # Manual check for whitespace-only message
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "message"],
                    "msg": "Message cannot be empty or consist only of whitespace",
                    "type": "value_error",
                }
            ],
        )

    # Use the validated API key to verify ownership
    owner_identifier = api_key

    conversation = db.get(Conversation, conversation_id)
    if not conversation or conversation.owner_identifier != owner_identifier:
        logger.warning(f"Conversation {conversation_id} not found or access denied for owner {owner_identifier}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not ai_agent:
        logger.error(f"Chat request failed for conversation {conversation_id}: Agent not available.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available. Please check server configuration.",
        )

    # --- Fetch message history ---
    statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.timestamp)
    )
    db_messages = db.exec(statement).all()

    # Convert DB messages to PydanticAI format
    message_history: List[ModelMessage] = []
    for msg in db_messages:
        message_history.append(ModelMessage(role=msg.role, content=msg.content))
    logger.debug(f"Retrieved {len(message_history)} messages for conversation {conversation_id}")

    # --- Store user message ---
    user_message = ConversationMessage(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        timestamp=datetime.utcnow(),
    )
    db.add(user_message)

    # --- Interact with AI agent ---
    try:
        logger.debug(f"Running agent for conversation {conversation_id} with history length {len(message_history)}")
        agent_run_result = await ai_agent.run(message=request.message, message_history=message_history)

        # Extract the actual response data from the result wrapper
        response_data = agent_run_result.data

        if isinstance(response_data, ChatResponse):  # Reusing ChatResponse model here
            ai_reply = response_data.reply
            logger.info(f"AI Agent reply for conversation {conversation_id}: '{ai_reply[:50]}...'")

            # --- Store assistant message ---
            assistant_message = ConversationMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_reply,
                timestamp=datetime.utcnow(),
            )
            db.add(assistant_message)

            # Commit both messages
            db.commit()
            logger.debug(f"Stored user and assistant messages for conversation {conversation_id}")

            return NewMessageResponse(reply=ai_reply)
        else:
            # Handle unexpected response type
            error_msg = f"Agent returned unexpected data type for conversation {conversation_id}: {type(response_data)}"
            logger.error(error_msg)
            # Rollback the user message storage
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI agent returned an unexpected response format.",
            )

    except Exception as e:
        logger.exception(f"Error during agent run for conversation {conversation_id}: {e}")
        # Rollback the user message storage
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error processing request: {e}",
        )
