#!/usr/bin/env python3
"""
Example MCP client for connecting to the PydanticAI API Template MCP server.

This example demonstrates how to:
1. Connect to the MCP server
2. Use the chat tool

Prerequisites:
- pydantic-ai[mcp] installed
- An OpenAI API key in your environment
- The MCP server running (pat run-mcp)
"""

import asyncio

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

# Load environment variables from .env file
load_dotenv()

# Define the MCP server URL - change if using a different port
MCP_SERVER_URL = "http://localhost:3001/sse"


async def main() -> None:
    # Create an MCP server client
    server = MCPServerHTTP(url=MCP_SERVER_URL)

    # Create a PydanticAI agent with the MCP server
    agent = Agent("openai:gpt-4o", mcp_servers=[server])

    # Run the agent with access to the MCP server
    async with agent.run_mcp_servers():
        print("\nAsking the MCP server a question...")

        # This will use the chat tool from the MCP server
        result = await agent.run("What are the top 3 features of PydanticAI?")

        # Print the result
        print("\nResult from MCP server:")
        print(result.data)

        # You can ask more questions
        print("\nAsking another question...")
        result = await agent.run("How can I use PydanticAI with FastAPI?")
        print("\nResult from MCP server:")
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
