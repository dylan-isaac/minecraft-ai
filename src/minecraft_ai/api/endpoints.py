import logging
import os
import sys  # Import sys to configure logging output stream
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import logfire

# Load environment variables from .env file BEFORE other imports
# This ensures they are available when other modules might need them
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from minecraft_ai.api.models import (
    ChatMessage,
    ChatResponse,
)
from minecraft_ai.utils.observability import (
    instrument_all_agents,
    setup_logfire,
    shutdown_logfire,
)

# Import agent instance and initialization function
from ..agents import ai_agent, initialize_agents

# Import and include routers for modular endpoints
from .routers import chat, minecraft  # Assuming chat and minecraft routers exist

# Import security dependency
from .security import verify_api_key

load_dotenv()


# Initialize LogFire if enabled - MOVED: Now called after app creation

# --- Logging Configuration ---
# Consistent logging setup from axe-ai
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),  # Allow configuring level via env var
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MINECRAFT_AI_API_KEY = os.getenv("MINECRAFT_AI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning(
        "OPENAI_API_KEY environment variable not set (or not found in .env). The /chat endpoint will not work."
    )


# --- FastAPI App ---
# Define lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handles application startup and shutdown events."""
    logfire.info("Application startup")
    # Initialize PydanticAI agents
    initialize_agents()
    # Instrument all PydanticAI agents at startup
    instrument_all_agents()
    yield
    # Shutdown logic here
    logfire.info("Application shutdown initiated")
    shutdown_logfire()  # Call logfire shutdown


app = FastAPI(
    title="Minecraft AI",
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

# --- Routers ---
# Import and include routers for modular endpoints
app.include_router(chat.router)
app.include_router(minecraft.router)


# --- API Endpoints ---
@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage, authorized: bool = Depends(verify_api_key)) -> ChatResponse:
    """Endpoint to chat with the PydanticAI agent."""
    # Proceed with the agent logic using the validated chat_message (provided by FastAPI)
    with logfire.span("chat_with_agent", operation_type="chat", model="gpt-4o") as span:
        # Split user_message assignment to avoid line too long
        user_msg = chat_message.message[:100]
        if len(chat_message.message) > 100:
            user_msg += "..."
        span.set_attributes(
            {
                "message_length": len(chat_message.message),
                "user_message": (
                    f"{chat_message.message[:100]}..." if len(chat_message.message) > 100 else chat_message.message
                ),
                "endpoint": "/chat",
                "prompt_type": "chat_completion",
            }
        )
        logger.info(f"Received chat request: '{chat_message.message[:50]}...'")

        if not ai_agent:
            logger.error("Chat request failed: PydanticAI Agent not initialized or OpenAI key missing.")
            span.set_attributes({"error": True, "error.message": "AI service not available"})
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail=("AI service is not available. Please check server configuration."),
            )

        try:
            logger.debug(f"Running PydanticAI chat agent for message: {chat_message.message[:50]}...")
            # Explicitly assert that ai_agent is not None to satisfy type checker
            assert ai_agent is not None

            # Use the initialized agent to get a response
            agent_run_result = await ai_agent.run(chat_message.message)

            # Extract the actual response data from the result wrapper
            response_data = agent_run_result.data

            # Check if the data is the expected ChatResponse type
            if isinstance(response_data, ChatResponse):
                response = response_data
                # Log the reply for debugging/visibility
                logger.info(f"AI Agent reply: '{response.reply[:50]}...'")
                span.set_attributes(
                    {
                        "response_length": len(response.reply),
                        "success": True,
                        "completion_type": "chat",
                    }
                )
                return response
            else:
                # Handle unexpected response type
                error_msg = f"Agent returned unexpected data type: {type(response_data)}"
                logger.error(error_msg)
                span.set_attributes({"error": True, "error.message": error_msg})
                raise HTTPException(
                    status_code=500,
                    detail="AI agent returned an unexpected response format.",
                )

        except Exception as e:
            logger.exception(f"Error during PydanticAI agent run: {e}")
            span.set_attributes(
                {
                    "error": True,
                    "error.message": f"Agent execution error: {e}",
                    "error.type": type(e).__name__,
                }
            )
            raise HTTPException(status_code=500, detail=f"Internal server error processing request: {e}")
