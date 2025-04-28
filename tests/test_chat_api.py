import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient
from minecraft_ai.api.endpoints import app  # Will be updated to import the chat router
from minecraft_ai.api.models import (
    ChatResponse,
)
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# --- Test API Key ---
TEST_API_KEY = "test_key_123"


@pytest.fixture(scope="session", autouse=True)
def set_test_api_key_env():
    os.environ["MINECRAFT_AI_API_KEY"] = TEST_API_KEY
    yield
    del os.environ["MINECRAFT_AI_API_KEY"]


# --- Fixtures ---
@pytest_asyncio.fixture(scope="session")
def test_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest_asyncio.fixture(scope="function")
def test_session(test_engine):
    with Session(test_engine) as session:
        yield session


@pytest_asyncio.fixture(scope="function", autouse=True)
def override_get_session(test_session):
    from minecraft_ai.database import database

    def _get_test_session():
        yield test_session

    app.dependency_overrides[database.get_session] = _get_test_session
    yield
    app.dependency_overrides.pop(database.get_session, None)


@pytest_asyncio.fixture
def async_client():
    transport = ASGITransport(app=app)

    async def _client():
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac

    return _client


@pytest.fixture(autouse=True)
def clear_rate_limit_store():
    # Import the rate limiter store and clear it before each test
    from minecraft_ai.api.routers import chat

    if hasattr(chat, "_rate_limit_store"):
        chat._rate_limit_store.clear()


# --- Helper for API requests with key ---
def with_api_key(headers=None):
    h = {"X-API-Key": TEST_API_KEY}
    if headers:
        h.update(headers)
    return h


# --- Test: POST /chats ---
@pytest.mark.asyncio
@patch("minecraft_ai.api.endpoints.ai_agent", new_callable=AsyncMock)
async def test_create_conversation_success(mock_agent, async_client):
    """
    Test creating a new conversation returns ConversationInfo with id and created_at.
    Assumes API key is valid or not required for test.
    """
    payload = {"topic": "Test Topic"}
    async for ac in async_client():
        response = await ac.post("/chats", json=payload, headers=with_api_key())
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["topic"] == "Test Topic"
        assert "created_at" in data


@pytest.mark.asyncio
async def test_create_conversation_default_topic(async_client):
    """
    Test creating a conversation with no topic sets topic to None or default.
    """
    async for ac in async_client():
        response = await ac.post("/chats", json={}, headers=with_api_key())
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["topic"] is None or data["topic"] == ""


# --- Test: GET /chats ---
@pytest.mark.asyncio
async def test_list_conversations_success(async_client):
    """
    Test listing conversations returns only those for the implicit owner.
    """
    async for ac in async_client():
        response = await ac.get("/chats", headers=with_api_key())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)


@pytest.mark.asyncio
async def test_list_conversations_filter_by_player_uuid(async_client):
    async for ac in async_client():
        await ac.post(
            "/chats", json={"topic": "A", "player_uuid": "uuid1", "player_username": "user1"}, headers=with_api_key()
        )
        await ac.post(
            "/chats", json={"topic": "B", "player_uuid": "uuid2", "player_username": "user2"}, headers=with_api_key()
        )
        resp = await ac.get("/chats?player_uuid=uuid1", headers=with_api_key())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["player_uuid"] == "uuid1"


@pytest.mark.asyncio
async def test_list_conversations_filter_by_player_username(async_client):
    async for ac in async_client():
        await ac.post(
            "/chats", json={"topic": "C", "player_uuid": "uuid3", "player_username": "user3"}, headers=with_api_key()
        )
        await ac.post(
            "/chats", json={"topic": "D", "player_uuid": "uuid4", "player_username": "user4"}, headers=with_api_key()
        )
        resp = await ac.get("/chats?player_username=user4", headers=with_api_key())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["player_username"] == "user4"


@pytest.mark.asyncio
async def test_rate_limiting(async_client):
    async for ac in async_client():
        for _ in range(10):
            resp = await ac.post("/chats", json={"topic": "RLTest"}, headers=with_api_key())
            assert resp.status_code in (200, 201)
        resp = await ac.post("/chats", json={"topic": "RLTest"}, headers=with_api_key())
        assert resp.status_code == 429
        assert "rate limit" in resp.text.lower()


# --- Test: POST /chats/{conversation_id}/messages ---
@pytest.mark.asyncio
@patch("minecraft_ai.api.routers.chat.ai_agent", new_callable=AsyncMock)
async def test_add_message_success(mock_agent, async_client):
    """
    Test adding a message to a conversation stores user/assistant messages and returns reply.
    Mocks the agent to return a canned response.
    """
    async for ac in async_client():
        create_resp = await ac.post("/chats", json={"topic": "Chat"}, headers=with_api_key())
        conv_id = create_resp.json()["id"]
        mock_agent.run.return_value.data = ChatResponse(reply="Hello from AI")
        payload = {"message": "Hi AI!"}
        response = await ac.post(f"/chats/{conv_id}/messages", json=payload, headers=with_api_key())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["reply"] == "Hello from AI"


@pytest.mark.asyncio
async def test_add_message_invalid_conversation(async_client):
    """
    Test adding a message to a nonexistent conversation returns 404.
    """
    async for ac in async_client():
        payload = {"message": "Hi AI!"}
        response = await ac.post("/chats/9999/messages", json=payload, headers=with_api_key())
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@patch("minecraft_ai.api.routers.chat.ai_agent", new_callable=AsyncMock)
async def test_add_message_empty_message(mock_agent, async_client):
    """
    Test adding an empty message returns 422 (validation error).
    """
    async for ac in async_client():
        create_resp = await ac.post("/chats", json={}, headers=with_api_key())
        conv_id = create_resp.json()["id"]
        mock_agent.run.return_value.data = ChatResponse(reply="Hello from AI")
        payload = {"message": "   "}
        response = await ac.post(f"/chats/{conv_id}/messages", json=payload, headers=with_api_key())
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
@patch("minecraft_ai.api.endpoints.ai_agent", None)
async def test_add_message_agent_unavailable(async_client):
    """
    Test adding a message when the agent is unavailable returns 503.
    """
    async for ac in async_client():
        create_resp = await ac.post("/chats", json={}, headers=with_api_key())
        conv_id = create_resp.json()["id"]
        payload = {"message": "Hi AI!"}
        response = await ac.post(f"/chats/{conv_id}/messages", json=payload, headers=with_api_key())
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# --- Test: API Key Required (missing/invalid) ---
@pytest.mark.asyncio
async def test_api_key_missing(async_client):
    async for ac in async_client():
        response = await ac.post("/chats", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API key required" in response.text


@pytest.mark.asyncio
async def test_api_key_invalid(async_client):
    async for ac in async_client():
        response = await ac.post("/chats", json={}, headers={"X-API-Key": "wrong_key"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid API key" in response.text


# --- Additional edge cases and error handling can be added as endpoints are implemented ---
