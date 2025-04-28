import logging
import os
from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

# Models needed for agent initialization
from .api.models import ChatResponse

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Global agent instances - initialized once
ai_agent: Optional[Agent] = None


def initialize_agents():
    """Initializes the global PydanticAI agents.

    Should be called once during application startup (e.g., in lifespan context).
    Handles potential errors during initialization.
    """
    global ai_agent

    if ai_agent is not None:
        logger.debug("Agents already initialized.")
        return

    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY environment variable not set. AI Agent will not be initialized.")
        return

    try:
        minecraft_system_prompt = (
            "You are a helpful and friendly Minecraft assistant. "
            "Your goal is to answer questions about Minecraft gameplay, items, blocks, mobs, crafting recipes, and "
            " mechanics to help make playing Minecraft more enjoyable. "
            "When asked for information you don't know, use the search tool provided. "
            "Prioritize information from official sources like minecraft.wiki."
        )

        ai_agent = Agent(
            "openai:gpt-4.1",
            result_type=ChatResponse,
            system_prompt=minecraft_system_prompt,
            tools=[duckduckgo_search_tool()],
            instrument=True,  # Assuming Logfire instrumentation is desired
        )
        logger.info("PydanticAI Agent initialized with openai:gpt-4.1")

    except ImportError as e:
        logger.error(f"Failed to import PydanticAI dependencies (likely openai): {e}")
        logger.error("Ensure 'pydantic-ai[openai]' is installed correctly.")
        ai_agent = None
    except Exception:
        logger.exception("Unexpected error initializing PydanticAI Agent:")
        ai_agent = None


# Example of how to potentially add other agents if needed
# story_agent: Optional[Agent] = None
# def initialize_story_agent(): ...
