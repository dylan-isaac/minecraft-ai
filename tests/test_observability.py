"""Tests for the observability module."""

import os
from unittest.mock import MagicMock, patch

from pydanticai_api_template.utils.observability import (
    is_logfire_enabled,
    setup_logfire,
    shutdown_logfire,
)


def test_is_logfire_enabled() -> None:
    """Test the is_logfire_enabled function."""
    # Test when disabled (default)
    if "LOGFIRE_ENABLED" in os.environ:
        del os.environ["LOGFIRE_ENABLED"]
    assert is_logfire_enabled() is False

    # Test when enabled
    os.environ["LOGFIRE_ENABLED"] = "true"
    assert is_logfire_enabled() is True

    # Test case insensitive
    os.environ["LOGFIRE_ENABLED"] = "TRUE"
    assert is_logfire_enabled() is True

    # Test alternative values
    os.environ["LOGFIRE_ENABLED"] = "1"
    assert is_logfire_enabled() is True
    os.environ["LOGFIRE_ENABLED"] = "yes"
    assert is_logfire_enabled() is True

    # Test when disabled
    os.environ["LOGFIRE_ENABLED"] = "false"
    assert is_logfire_enabled() is False
    os.environ["LOGFIRE_ENABLED"] = "0"
    assert is_logfire_enabled() is False


@patch("pydanticai_api_template.utils.observability.logfire")
@patch(
    "pydanticai_api_template.utils.observability.configure_pydantic_ai_instrumentation"
)
def test_setup_logfire_disabled(
    mock_configure: MagicMock, mock_logfire: MagicMock
) -> None:
    """Test setup_logfire when LogFire is disabled."""
    # Ensure LogFire is disabled
    os.environ["LOGFIRE_ENABLED"] = "false"

    # Call the function
    setup_logfire()

    # Verify no calls to logfire
    mock_logfire.configure.assert_not_called()
    mock_configure.assert_not_called()


@patch("pydanticai_api_template.utils.observability.logfire")
@patch(
    "pydanticai_api_template.utils.observability.configure_pydantic_ai_instrumentation"
)
@patch("pydanticai_api_template.utils.observability.HAS_PYDANTIC_AI_INTEGRATION", True)
def test_setup_logfire_enabled(
    mock_configure: MagicMock, mock_logfire: MagicMock
) -> None:
    """Test setup_logfire when LogFire is enabled via LOGFIRE_TOKEN."""
    # Enable LogFire and set token
    os.environ["LOGFIRE_ENABLED"] = "true"
    os.environ["LOGFIRE_TOKEN"] = "test-token"
    # Ensure API key/project ID are not set (or remove if they are)
    os.environ.pop("LOGFIRE_API_KEY", None)
    os.environ.pop("LOGFIRE_PROJECT_ID", None)

    # Call the function
    setup_logfire(service_name="test-service", environment="test")

    # Verify configuration using token
    mock_logfire.configure.assert_called_once_with(
        token="test-token",
        service_name="test-service",
        environment="test",
    )

    # Verify instrumentation
    mock_logfire.instrument_httpx.assert_called_once()
    # mock_logfire.instrument_fastapi.assert_called_once()
    # Removed: Not called without app
    mock_configure.assert_called_once()


@patch("pydanticai_api_template.utils.observability.logfire")
def test_shutdown_logfire_disabled(mock_logfire: MagicMock) -> None:
    """Test shutdown_logfire when LogFire is disabled."""
    # Ensure LogFire is disabled
    os.environ["LOGFIRE_ENABLED"] = "false"

    # Call the function
    shutdown_logfire()

    # Verify no calls to logfire
    mock_logfire.shutdown.assert_not_called()


@patch("pydanticai_api_template.utils.observability.logfire")
def test_shutdown_logfire_enabled(mock_logfire: MagicMock) -> None:
    """Test shutdown_logfire when LogFire is enabled."""
    # Enable LogFire
    os.environ["LOGFIRE_ENABLED"] = "true"

    # Call the function
    shutdown_logfire()

    # Verify shutdown was called
    mock_logfire.info.assert_called_once_with("Shutting down LogFire")
    mock_logfire.shutdown.assert_called_once()


@patch("pydanticai_api_template.utils.observability.logfire")
@patch(
    "pydanticai_api_template.utils.observability.configure_pydantic_ai_instrumentation"
)
@patch("pydanticai_api_template.utils.observability.HAS_PYDANTIC_AI_INTEGRATION", True)
def test_setup_logfire_promptfoo(
    mock_configure: MagicMock, mock_logfire: MagicMock
) -> None:
    """Test setup_logfire when called from prompt_test command via LOGFIRE_TOKEN."""
    # Enable LogFire and set token
    os.environ["LOGFIRE_ENABLED"] = "true"
    os.environ["LOGFIRE_TOKEN"] = "test-token-promptfoo"
    # Ensure API key/project ID are not set (or remove if they are)
    os.environ.pop("LOGFIRE_API_KEY", None)
    os.environ.pop("LOGFIRE_PROJECT_ID", None)

    # Call the function with promptfoo-testing service name
    setup_logfire(service_name="promptfoo-testing")

    # Verify configuration with correct service name using token
    mock_logfire.configure.assert_called_once_with(
        token="test-token-promptfoo",
        service_name="promptfoo-testing",
        environment=os.getenv("ENVIRONMENT", "development"),
    )

    # Verify instrumentation
    mock_logfire.instrument_httpx.assert_called_once()
    # mock_logfire.instrument_fastapi.assert_called_once()
    # Removed: Not called without app
    mock_configure.assert_called_once()
