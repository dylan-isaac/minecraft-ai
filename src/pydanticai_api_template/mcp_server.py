import argparse
import logging
import os
from typing import Any, Optional, cast

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from pydantic_ai import Agent

from pydanticai_api_template.api.models import (
    ChatResponse,
    StoryResponse,
)
from pydanticai_api_template.utils.observability import (
    instrument_all_agents,
    is_logfire_enabled,
)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the OpenAI agent
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize LogFire if enabled - moved to create_app function
# setup_logfire(service_name="pydanticai-mcp-server")

# Instrument all PydanticAI agents if Logfire is enabled
if is_logfire_enabled():
    instrument_all_agents()


# Initialize AI agent using imported models
try:
    ai_agent: Optional[Agent] = (
        Agent(
            "openai:gpt-4o",
            result_type=ChatResponse,
            instrument=is_logfire_enabled(),
        )
        if OPENAI_API_KEY
        else None
    )

    # Initialize story agent using imported models
    story_agent: Optional[Agent] = (
        Agent(
            "openai:gpt-4o",
            result_type=StoryResponse,
            instrument=is_logfire_enabled(),
        )
        if OPENAI_API_KEY
        else None
    )

    if ai_agent:
        logger.info("PydanticAI Agent initialized with openai:gpt-4o for MCP server")
    else:
        logger.warning(
            "PydanticAI Agent not initialized due to missing OPENAI_API_KEY."
        )
except Exception as e:
    logger.exception(f"Error initializing PydanticAI Agent: {e}")
    ai_agent = None
    story_agent = None

# Create FastMCP server
server = FastMCP("PydanticAI API MCP Server")


@server.tool()
async def chat(message: str) -> str:
    """Chat with the AI assistant

    Send a message to the AI assistant and receive a response.
    """
    with logfire.span(
        "mcp_chat", message=message[:100], operation_type="chat", model="gpt-4o"
    ) as span:
        if not ai_agent:
            span.set_attributes(
                {"error": True, "error.message": "AI service not available"}
            )
            return "AI service is not available. Please check server configuration."

        try:
            # Ensure the agent is properly typed for mypy
            assert ai_agent is not None

            # Track token count for the prompt
            span.set_attributes(
                {
                    "token_count_approx": len(message.split()),
                    "prompt_type": "user_message",
                }
            )

            result: Any = await ai_agent.run(message)

            # Properly handle the response based on its type
            # Access reply attribute directly from the ChatResponse object
            response_data = result.data
            if isinstance(response_data, ChatResponse):
                reply = str(response_data.reply)
                span.set_attributes(
                    {
                        "response_length": len(reply),
                        "response_token_count_approx": len(reply.split()),
                        "completion_type": "text",
                    }
                )
                return reply

            # Fallback if the structure doesn't match ChatResponse
            logger.warning(f"MCP Chat: Unexpected result type: {type(response_data)}")
            reply = str(response_data)
            span.set_attributes(
                {
                    "response_length": len(reply),
                    "response_token_count_approx": len(reply.split()),
                    "completion_type": "raw",
                    "warning": "Unexpected result structure, expected ChatResponse",
                }
            )
            return reply
        except Exception as e:
            logger.exception(f"Error in MCP chat tool: {e}")
            span.set_attributes({"error": True, "error.message": str(e)})
            return f"An error occurred while processing your request: {str(e)}"


@server.tool()
async def story(message: str) -> dict[str, Any]:
    """Generate a creative story idea

    Generate a story idea with a title and premise based on the input.
    You can specify genre, themes, or characters.

    Examples:
    - "Give me a sci-fi story about time travel"
    - "Create a fantasy story with dragons"
    - "Write a mystery set in Victorian London"
    """
    with logfire.span(
        "mcp_story",
        message=message[:100],
        operation_type="story_generation",
        model="gpt-4o",
    ) as span:
        if not story_agent:
            span.set_attributes(
                {"error": True, "error.message": "AI service not available"}
            )
            return {
                "error": (
                    "AI service is not available. Please check server configuration."
                )
            }

        try:
            # Enhance the prompt to get high-quality story ideas
            enhanced_prompt = (
                f"Generate a creative and original story idea based on this input: "
                f"{message}"
            )

            # Track token count for the prompt
            span.set_attributes(
                {
                    "token_count_approx": len(enhanced_prompt.split()),
                    "prompt_type": "structured_generation",
                    "input_length": len(message),
                }
            )

            # Ensure the agent is properly typed for mypy
            assert story_agent is not None

            result: Any = await story_agent.run(enhanced_prompt)

            # Explicitly type response_data to help mypy
            response_data: Any = result.data

            # Return the story idea as a dictionary
            # Check if the result is the expected StoryResponse object
            if isinstance(response_data, StoryResponse):
                # Convert StoryResponse to dict for MCP return type consistency
                story_dict = response_data.model_dump()
                span.set_attributes(
                    {
                        "story_title": story_dict.get("title", "N/A"),
                        "premise_length": len(story_dict.get("premise", "")),
                        "completion_type": "structured",
                        "response_complexity": (
                            "high"
                            if len(story_dict.get("premise", "")) > 200
                            else "medium"
                        ),
                    }
                )
                return cast(dict[str, Any], story_dict)
            # Fallback: if response_data is a dict, return as error-wrapped dict
            if isinstance(response_data, dict):
                logger.warning(f"MCP Story: Unexpected dict result: {response_data}")
                span.set_attributes(
                    {
                        "error": True,
                        "error.message": (
                            "Unexpected dict result, expected StoryResponse"
                        ),
                        "warning": ("Unexpected dict result, expected StoryResponse"),
                    }
                )
                return cast(
                    dict[str, Any],
                    {
                        "error": "Unexpected dict result from story agent",
                        "data": response_data,
                    },
                )
            # Fallback: return error for any other type
            logger.warning(f"MCP Story: Unexpected result type: {type(response_data)}")
            span.set_attributes(
                {
                    "error": True,
                    "error.message": "Failed to generate proper story idea structure",
                    "warning": "Unexpected result structure, expected StoryResponse",
                }
            )
            return cast(
                dict[str, Any],
                {
                    "error": "Failed to generate a proper story idea structure",
                    "data_type": str(type(response_data)),
                },
            )
        except Exception as e:
            logger.exception(f"Error in MCP story tool: {e}")
            span.set_attributes({"error": True, "error.message": str(e)})
            return cast(
                dict[str, Any],
                {"error": f"An error occurred while processing your request: {str(e)}"},
            )


def create_app() -> FastAPI:
    """Create a FastAPI app with the MCP server"""
    # Initialize FastAPI app first
    app = FastAPI(
        title="PydanticAI MCP Server",
        description="MCP server for PydanticAI API Template",
        version="0.1.0",
    )

    # Get the SSE app/routes from FastMCP
    sse_app = server.sse_app()

    # Mount the SSE app directly at the root
    # Since introspection showed the internal route is already /sse via the MCP service
    app.mount("/", sse_app, name="mcp_sse_root")
    logger.info("Mounted sse_app at / based on discovered internal route /sse")

    # Instrument with LogFire
    if is_logfire_enabled():
        from pydanticai_api_template.utils.observability import setup_logfire

        setup_logfire(service_name="pydanticai-mcp-server", app=app)

    return app


def run_standalone() -> None:
    """Run the MCP server standalone in SSE mode"""
    import uvicorn

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the MCP server")
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        help="Host to bind the server to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "3001")),
        help="Port to bind the server to",
    )
    args = parser.parse_args()

    host = args.host
    port = args.port

    logger.info(f"Starting MCP server on {host}:{port}")
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    run_standalone()
