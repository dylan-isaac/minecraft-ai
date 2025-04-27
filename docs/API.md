# API Reference

This document provides reference documentation for the Minecraft AI's endpoints.

## Base URL

All API endpoints are relative to the base URL:

- **Development**: `http://localhost:8000`
- **Production**: Your deployed URL

## Authentication

The API uses API key authentication to protect endpoints. Include your API key in the `X-API-Key` header with each request:

```http
X-API-Key: your_api_key_here
```

### Generating an API Key

Use the CLI tool to generate a secure API key:

```bash
pat generate-api-key
```

This will generate a random API key with the format `pydanticai_<random_hex>`. Add this key to your `.env` file:

```env
PYDANTICAI_API_KEY="your_generated_key"
```

If no API key is set in the environment, authentication will be skipped with a warning in the logs (suitable for development, but not recommended for production).

## Endpoints

### GET /

**Description**: Simple root endpoint that returns a welcome message.

**Response**:

```json
{
  "message": "Welcome to the Minecraft AI!"
}
```

### POST /chat

**Description**: Sends a message to the PydanticAI agent and receives a structured reply.

**Request**:

```json
{
  "message": "Your message to the AI agent"
}
```

**Response**:

```json
{
  "reply": "The AI agent's response"
}
```

**Notes**:

- Requires `OPENAI_API_KEY` environment variable to be set
- Uses the `gpt-4o` model by default

### POST /story

**Description**: Generates a story idea with a title and premise based on the user's input.

**Request**:

```json
{
  "message": "Give me a sci-fi story about time travel"
}
```

**Response**:

```json
{
  "title": "Echoes of Tomorrow",
  "premise": "A physicist discovers that time isn't linear but layered, with each moment existing simultaneously. When she builds a device to view these layers, she witnesses a future catastrophe and must find a way to reach across time to prevent it."
}
```

**Notes**:

- Requires `OPENAI_API_KEY` environment variable to be set
- Uses the `gpt-4o` model by default
- Input can specify genre, themes, or characters to guide the story idea generation

## Error Responses

The API uses standard HTTP status codes to indicate the success or failure of a request.

### Common Error Codes

- **400 Bad Request**: Invalid request format
- **401 Unauthorized**: Invalid or missing API key
- **500 Internal Server Error**: Server-side error
- **502 Bad Gateway**: Error communicating with LLM provider
- **503 Service Unavailable**: AI service is not available (e.g., missing API key)

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Interactive Documentation

When the server is running, you can access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These provide a user-friendly interface to explore the API, view request/response schemas, and test endpoints directly.

## Rate Limiting

No rate limiting is implemented in the template by default. In a production environment, you should add appropriate rate limiting based on your use case.

## Extending the API

To add new endpoints, see the [Developer Guide](./DEVELOPER.md) for instructions.

## MCP Server

The project includes an MCP (Model Context Protocol) server that allows AI agents to interact with our API.

### MCP Endpoint

- **URL**: `http://localhost:3001/sse`
- **Transport**: HTTP Server-Sent Events (SSE)

### Available Tools

| Tool Name | Description                | Parameters                                                          |
| --------- | -------------------------- | ------------------------------------------------------------------- |
| `chat`    | Chat with the AI assistant | `message`: The message to send to the assistant                     |
| `story`   | Generate a story idea      | `message`: The input to guide story generation (e.g., genre, theme) |

### Example Usage

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

# Connect to the MCP server
server = MCPServerHTTP(url='http://localhost:3001/sse')
agent = Agent('openai:gpt-4o', mcp_servers=[server])

async def main():
    async with agent.run_mcp_servers():
        # Chat example
        chat_result = await agent.run('Your message here')
        print(chat_result.data)

        # Story generation example
        story_result = await agent.run_tool('story', message='Create a sci-fi story about time travel')
        print(f"Title: {story_result['title']}")
        print(f"Premise: {story_result['premise']}")
```

### Adding Custom Tools

To add custom tools to the MCP server, edit the `/app/src/minecraft_ai/mcp_server.py` file and add new tool functions using the `@server.tool()` decorator:

```python
@server.tool()
async def your_tool_name(param1: str, param2: int) -> str:
    """Your tool description

    More detailed description here.
    """
    # Tool implementation
    return "Result"
```

### Running the MCP Server

To start the MCP server:

```bash
pat run-mcp
```

By default, the server runs on `0.0.0.0:3001`. You can customize the host and port:

```bash
pat run-mcp --host 127.0.0.1 --port 4000
```
