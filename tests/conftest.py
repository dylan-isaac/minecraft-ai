"""
Pytest configuration file for the minecraft_ai package tests.

This file contains pytest configuration for the test suite, including
environment setup and test fixtures that are used across multiple test files.
"""

import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Add the project root to the Python path
# This ensures imports work correctly during testing
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
# These are used in tests when real API keys are not available
os.environ.setdefault("OPENAI_API_KEY", "test_key_for_mocks")


@pytest.fixture(scope="function")
def env_setup(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """
    Set up environment variables for tests and restore them after.

    This fixture runs automatically for all tests and ensures environment
    variables are properly set and restored.
    """
    # Store original environment variables
    original_env = os.environ.copy()

    # Set up test environment
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce logging noise during tests

    yield

    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)
