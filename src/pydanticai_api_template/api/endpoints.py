import logging
import os
import sys  # Import sys to configure logging output stream
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

import logfire

# Load environment variables from .env file BEFORE other imports
# This ensures they are available when other modules might need them
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic_ai import Agent

from pydanticai_api_template.api.models import (
    ChatMessage,
    ChatResponse,
    StoryIdea,
)
from pydanticai_api_template.utils.observability import (
    instrument_all_agents,
    setup_logfire,
    shutdown_logfire,
)

load_dotenv()


# Initialize LogFire if enabled - MOVED: Now called after app creation

# --- Logging Configuration ---
# Consistent logging setup from axe-ai
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),  # Allow configuring level via env var
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - "
    "%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PYDANTICAI_API_KEY = os.getenv("PYDANTICAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning(
        "OPENAI_API_KEY environment variable not set (or not found in .env). "
        "The /chat endpoint will not work."
    )

# --- API Key Authentication ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> bool:
    """Verify the API key for protected endpoints.

    Returns True if the key is valid, raises HTTPException if not.
    When no API key is set in the environment, authentication is skipped (with warning).
    """
    if not PYDANTICAI_API_KEY:
        # Skip auth if no key is set (with warning)
        logger.warning(
            "API key validation skipped - no PYDANTICAI_API_KEY set in environment"
        )
        return True

    if api_key != PYDANTICAI_API_KEY:
        # If API key doesn't match, raise 401 Unauthorized
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid API key. Please provide a valid key in the X-API-Key header."
            ),
        )

    return True


# --- Pydantic Models ---
# Models moved to src/pydanticai_api_template/api/models.py

# --- PydanticAI Agent ---
# Initialize agents in the module scope so they are accessible by endpoints
try:
    # Use a more robust initialization
    ai_agent: Optional[Agent] = (
        Agent("openai:gpt-4o", result_type=ChatResponse, instrument=True)
        if OPENAI_API_KEY
        else None
    )

    # Initialize a specialized agent for story ideas
    story_agent: Optional[Agent] = (
        Agent("openai:gpt-4o", result_type=StoryIdea, instrument=True)
        if OPENAI_API_KEY
        else None
    )

    if ai_agent:
        logger.info("PydanticAI Agent initialized with openai:gpt-4o")
    else:
        logger.warning(
            "PydanticAI Agent not initialized due to missing OPENAI_API_KEY."
        )
except ImportError as e:
    logger.error(f"Failed to import PydanticAI dependencies (likely openai): {e}")
    logger.error("Ensure 'pydantic-ai[openai]' is installed correctly.")
    ai_agent = None  # Ensure agent is None if import fails
    story_agent = None  # Ensure story_agent is None if import fails
except Exception:
    logger.exception("Unexpected error initializing PydanticAI Agent:")
    ai_agent = None
    story_agent = None  # Ensure story_agent is None if exception occurs


# --- FastAPI App ---
# Define lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handles application startup and shutdown events."""
    logfire.info("Application startup")
    # Instrument all PydanticAI agents at startup
    instrument_all_agents()
    yield
    # Shutdown logic here
    logfire.info("Application shutdown initiated")
    shutdown_logfire()  # Call logfire shutdown


app = FastAPI(
    title="PydanticAI API Template",
    description="FastAPI project with PydanticAI integration.",
    version="0.1.0",
    lifespan=lifespan,  # Register the lifespan manager
)

# Initialize LogFire with the FastAPI app
setup_logfire(service_name="pydanticai-api", app=app)

# --- CORS Middleware ---
# Allow all origins for development, be more specific in production
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
logger.info(f"Allowing CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Read from env var or default to all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.get("/")
async def read_root() -> Dict[str, str]:
    """Basic root endpoint."""
    logger.info("Root endpoint '/' accessed.")
    logfire.info("Root endpoint accessed")
    return {"message": "Welcome to the PydanticAI API Template!"}


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    chat_message: ChatMessage, authorized: bool = Depends(verify_api_key)
) -> ChatResponse:
    """Endpoint to chat with the PydanticAI agent."""
    # Use logfire for structured logging with context
    with logfire.span(
        "chat_with_agent", operation_type="api_chat", model="gpt-4o"
    ) as span:
        span.set_attributes(
            {
                "message_length": len(chat_message.message),
                "user_message": chat_message.message[:100]
                + ("..." if len(chat_message.message) > 100 else ""),
                "token_count_approx": len(chat_message.message.split()),
                "endpoint": "/chat",
                "prompt_type": "user_message",
            }
        )

        logger.info(
            f"Received chat request: '{chat_message.message[:50]}...'"
        )  # Log truncated message

        if not ai_agent:
            logger.error(
                "Chat request failed: PydanticAI Agent not initialized or "
                "OpenAI key missing."
            )
            span.set_attributes(
                {"error": True, "error.message": "AI service not available"}
            )
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail=(
                    "AI service is not available. Please check server configuration."
                ),
            )

        try:
            logger.debug(
                f"Running PydanticAI agent for message: {chat_message.message[:50]}..."
            )
            # Explicitly assert that ai_agent is not None to satisfy type checker
            assert ai_agent is not None

            # Use the initialized agent
            agent_run_result = await ai_agent.run(chat_message.message)

            # Get response data
            response_data = agent_run_result.data

            # Check if result is already a ChatResponse or needs conversion
            if isinstance(response_data, ChatResponse):
                chat_response = response_data
            else:
                # Convert string or dict response to ChatResponse
                reply = str(response_data)
                chat_response = ChatResponse(reply=reply)

            span.set_attributes(
                {
                    "response_length": len(chat_response.reply),
                    "success": True,
                    "response_token_count_approx": len(chat_response.reply.split()),
                    "completion_type": "text",
                    "latency_ms": int(
                        (getattr(agent_run_result, "completion_time", 0) or 0) * 1000
                    ),
                }
            )

            logger.info("Agent returned reply.")
            return chat_response
        except Exception as e:
            # Catch-all for any other exceptions that might occur
            logger.exception(f"Error in chat_with_agent: {e}")
            span.set_attributes({"error": True, "error.message": str(e)})
            # We don't want to expose internal errors to clients
            raise HTTPException(
                status_code=500,
                detail=(
                    "An internal server error occurred while processing your request."
                ),
            )


@app.post("/story", response_model=StoryIdea)
async def generate_story_idea(
    chat_message: ChatMessage, authorized: bool = Depends(verify_api_key)
) -> StoryIdea:
    """Endpoint to generate a story idea with title and premise."""
    # Use logfire for structured logging with context
    with logfire.span(
        "generate_story_idea", operation_type="creative_generation", model="gpt-4o"
    ) as span:
        span.set_attributes(
            {
                "message_length": len(chat_message.message),
                "user_message": chat_message.message[:100]
                + ("..." if len(chat_message.message) > 100 else ""),
                "token_count_approx": len(chat_message.message.split()),
                "endpoint": "/story",
                "prompt_type": "structured_generation",
            }
        )

        logger.info(
            f"Received story idea request: '{chat_message.message[:50]}...'"
        )  # Log truncated message

        if not story_agent:
            logger.error(
                "Story idea request failed: PydanticAI Agent not initialized or "
                "OpenAI key missing."
            )
            span.set_attributes(
                {"error": True, "error.message": "AI service not available"}
            )
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail=(
                    "AI service is not available. Please check server configuration."
                ),
            )

        try:
            logger.debug(
                f"Running PydanticAI story agent for message: "
                f"{chat_message.message[:50]}..."
            )
            # Explicitly assert that story_agent is not None to satisfy type checker
            assert story_agent is not None

            # Enhance the prompt to get high-quality story ideas
            enhanced_prompt = (
                f"Generate a creative and original story idea based on this input: "
                f"{chat_message.message}"
            )

            # Use the initialized agent
            agent_run_result = await story_agent.run(enhanced_prompt)

            # Get the result data
            response_data = agent_run_result.data

            # Ensure we have a StoryIdea object
            if isinstance(response_data, StoryIdea):
                story_idea = response_data
                span.set_attributes(
                    {
                        "response_title": story_idea.title,
                        "response_premise_length": len(story_idea.premise),
                        "success": True,
                        "completion_type": "structured",
                        "latency_ms": int(
                            (getattr(agent_run_result, "completion_time", 0) or 0)
                            * 1000
                        ),
                    }
                )
                logger.info("Agent returned story idea.")
                return story_idea
            logger.error(f"Agent returned unexpected data type: {type(response_data)}")
            span.set_attributes(
                {"error": True, "error.message": "Invalid response format"}
            )
            raise HTTPException(
                status_code=500,
                detail="AI agent returned an unexpected response format.",
            )
        except Exception as e:
            logger.exception(f"Error generating story idea: {e}")
            span.set_attributes({"error": True, "error.message": str(e)})
            raise HTTPException(
                status_code=500,
                detail=(
                    "An internal server error occurred while processing your request."
                ),
            )
