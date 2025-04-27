"""
Tests for the MCP server functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from minecraft_ai.mcp_server import chat, create_app
from starlette.applications import Starlette
from starlette.routing import Mount


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI app for testing."""
    return create_app()


def test_create_app(app: FastAPI) -> None:
    """Test app creation, metadata, and correct SSE mounting."""
    # Basic app metadata checks
    assert app.title == "PydanticAI MCP Server"
    assert app.description == "MCP server for Minecraft AI"

    # Verify that the SSE app is mounted correctly at the root
    mount_route = None
    for route in app.routes:
        if isinstance(route, Mount) and route.path == "":
            mount_route = route
            break

    assert mount_route is not None, "No Mount found at root path ('')"
    assert isinstance(mount_route.app, (FastAPI, Starlette)), "Mounted app is not a FastAPI or Starlette instance"

    # Verify the mounted app has the /sse route internally
    sse_route_found = False
    for sub_route in mount_route.app.routes:
        route_path = getattr(sub_route, "path", str(sub_route))
        if "/sse" in route_path:
            sse_route_found = True
            break

    assert sse_route_found, "Internal route '/sse' not found in mounted SSE app"


@pytest.mark.asyncio
@patch("minecraft_ai.mcp_server.ai_agent")
async def test_chat_success(
    mock_ai_agent: MagicMock,
) -> None:
    """Test successful chat interaction."""
    mock_result = MagicMock()
    mock_result.data = "Mocked response"
    mock_ai_agent.run = AsyncMock(return_value=mock_result)
    response = await chat("Hello, how are you?")
    mock_ai_agent.run.assert_called_once_with("Hello, how are you?")
    assert response == "Mocked response"


@pytest.mark.asyncio
@patch("minecraft_ai.mcp_server.ai_agent", None)
async def test_chat_no_agent() -> None:
    """Test chat interaction when agent is not found."""
    response = await chat("Hello")
    assert "AI service is not available" in response


@pytest.mark.asyncio
@patch("minecraft_ai.mcp_server.ai_agent")
async def test_chat_exception(
    mock_ai_agent: MagicMock,
) -> None:
    """Test chat interaction when agent run raises an exception."""
    mock_ai_agent.run = AsyncMock(side_effect=Exception("Test exception"))
    response = await chat("Hello")
    assert "An error occurred" in response
    assert "Test exception" in response
