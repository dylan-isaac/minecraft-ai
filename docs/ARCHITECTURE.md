# Architecture

This document describes the system design and architecture of the Minecraft AI.

## System Overview

The Minecraft AI is built on the following key components:

```text
┌───────────────────────────────────────────────────────┐
│                     FastAPI App                        │
│                                                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │   Routes    │   │  Pydantic   │   │    API      │  │
│  │ (endpoints) │◄──┤   Models    │◄──┤   Logic     │  │
│  └─────────────┘   └─────────────┘   └─────────────┘  │
│           ▲                ▲                ▲         │
└───────────┼────────────────┼────────────────┼─────────┘
            │                │                │
            ▼                ▼                ▼
┌───────────────────────────────────────────────────────┐
│                    PydanticAI                         │
│                                                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │   Agent     │───┤  Structured │───┤     LLM     │  │
│  │ Definitions │   │  Responses  │   │ Integration │  │
│  └─────────────┘   └─────────────┘   └─────────────┘  │
│                                                       │
└───────────────────────────────────────────────────────┘
```

## Component Details

### FastAPI Application

The FastAPI application provides the web API interface and handles HTTP requests and responses.

- **Routes (endpoints.py)**: Defines the API endpoints and their behavior.
- **Pydantic Models (models.py)**: Defines the data models for requests and responses.
- **API Logic**: Business logic for processing requests and generating responses.

### PydanticAI Integration

PydanticAI provides a bridge between the API and LLMs, allowing structured interactions.

- **Agent Definitions**: Configures the PydanticAI agent for handling AI requests.
- **Structured Responses**: Uses Pydantic models to ensure type-safe, validated responses from LLMs.
- **LLM Integration**: Handles communication with underlying LLM services (like OpenAI).

### CLI Application

A command-line interface for managing the application, built with Typer.

- **Server Command**: Starts the FastAPI server.
- **Utility Commands**: Helper functions for validation, cleanup, etc.
- **Development Tools**: Commands to assist the development workflow.

### Minecraft Fabric Mod (Client-Side)

Located in the `minecraft-mod/` directory, this is a client-side Fabric mod written in Java, designed to run within the player's Minecraft game instance.

- **Purpose**: To provide an in-game interface for interacting with the AI backend. It adds custom chat commands (e.g., `/ai <prompt>`).
- **Interaction**: When a command is issued, the mod captures the player's context (like current coordinates for location-based commands) and the user's prompt.
- **Communication**: It sends an HTTP POST request to a dedicated endpoint on the FastAPI backend (e.g., `/minecraft/command`). This request includes the prompt, context data, and the necessary API key (`X-API-Key` header) for authentication.
- **Backend Processing**: The FastAPI backend receives the request, potentially interacts with PydanticAI for complex queries or a database (SQLite) for saving/retrieving data like coordinates.
- **Response Handling**: The mod receives the JSON response from the backend and displays the relevant information (e.g., AI response, confirmation message, retrieved coordinates) in the Minecraft chat interface.

```text
┌──────────────────┐      ┌───────────────────┐      ┌──────────────────┐
│ Minecraft Client │──────│  Fabric Mod       │──────│ FastAPI Backend  │
│ (with Mod)       │      │ (`minecraft-mod/`)│      │ (`src/`)         │
│ Issues `/ai` cmd │----->│ Captures context  │----->│ Receives Request │
│                  │      │ Sends HTTP POST   │      │ Processes Cmd    │
│                  │      │                   │      │ (DB / AI)      │
│ Receives Chat Msg│<-----│ Receives Response │<-----│ Sends Response   │
│                  │      │ Displays in Chat  │      │ (JSON)           │
└──────────────────┘      └───────────────────┘      └──────────────────┘
```

This architecture keeps the game-specific client logic separate from the core AI and API backend.

## Data Flow

1. Client sends a request to the API endpoint
2. FastAPI validates the request using Pydantic models
3. The endpoint handler processes the request and calls the PydanticAI agent
4. PydanticAI communicates with the LLM service using the request parameters
5. The LLM generates a response, which is parsed and validated by PydanticAI
6. The structured response is returned to the client

## Configuration Management

The application uses a hierarchical configuration approach:

1. Environment variables (highest priority)
2. .env file variables
3. Default values in code (lowest priority)

Key configuration options include:

- OPENAI_API_KEY: For LLM integration
- HOST/PORT: For server binding
- LOG_LEVEL: For log verbosity control

## Extensibility

The architecture is designed for extensibility:

1. **New LLM Providers**: Can be added by extending the PydanticAI configuration
2. **Additional Endpoints**: Can be easily added to endpoints.py
3. **New Models**: Can be defined in models.py to support new functionality
4. **CLI Commands**: Can be added to cli.py to support new operations

## MCP Server Architecture

The project includes an MCP (Model Context Protocol) server that exposes AI functionalities over a standardized protocol.

### Components

```text
                  ┌──────────────────┐
                  │   MCP Client     │
                  │  (Any Protocol-  │
                  │ Compatible Agent)│
                  └────────┬─────────┘
                           │
                           │ HTTP SSE
                           │ Connection
                           ▼
┌───────────────────────────────────────────────┐
│                 MCP Server                     │
│                                               │
│  ┌───────────────┐      ┌───────────────────┐ │
│  │  FastMCP      │◄────►│ AI Agent Tools    │ │
│  │  Server       │      │                   │ │
│  └───────┬───────┘      └─────────┬─────────┘ │
│          │                        │           │
│          │                        │           │
│          ▼                        ▼           │
│  ┌───────────────┐      ┌───────────────────┐ │
│  │  FastAPI      │      │ PydanticAI Agent  │ │
│  │  Integration  │      │                   │ │
│  └───────────────┘      └───────────────────┘ │
└───────────────────────────────────────────────┘
```

### Key Components

1. **MCP Server** (`mcp_server.py`):
   - Implements the Model Context Protocol server using FastMCP
   - Provides AI tools that can be called by any MCP-compatible client
   - Integrates with the FastAPI application for unified deployment

2. **AI Agent Tools**:
   - `chat`: Exposes the chat functionality to MCP clients
   - Extensible: New tools can be added using the `@server.tool()` decorator

3. **Transport Protocol**:
   - Uses HTTP Server-Sent Events (SSE) for network communication
   - Allows multiple clients to connect to the server remotely

### Advantages

- **Standardized Protocol**: Allows any MCP-compatible agent to access your API's functionalities
- **Decoupled Architecture**: MCP clients don't need to know API implementation details
- **Unified Development**: Same AI agents used in both REST API and MCP server
- **Extensibility**: Easy to add new tools without changing client code

- **Environment Variables:**
  - `LOGFIRE_TOKEN`: Required for production observability.
  - `OPENAI_API_KEY`: For LLM interactions.
  - `ANTHROPIC_API_KEY`: For Claude model access.

## Maintenance

Maintaining the project involves several key areas to ensure consistency, security, and optimal performance. Key maintenance activities include:

- **Dependency Management**: Use `uv` to manage Python dependencies in `pyproject.toml`.
- **Configuration Synchronization**: Run `make sync-configs` to update related configuration files (e.g., pre-commit hooks, VS Code tasks) after changes to `pyproject.toml` or CLI commands.
- **Docker Images**: Rebuild Docker images (`docker compose build`) after adding dependencies or modifying Dockerfiles.
- **CLI Updates**: Keep the `Makefile`, `README.md`, and potentially VS Code tasks (`.vscode/tasks.json` - though often handled by `make sync-configs`) synchronized with changes in `src/minecraft_ai/cli.py`.
- **Core Dependency Upgrades**: Follow a careful process when upgrading major dependencies like Python, FastAPI, or PydanticAI, including reviewing changelogs and thorough testing.

For detailed procedures on these and other maintenance tasks, such as managing the wishlist, updating VS Code settings, and modifying linting rules, refer to the [Project Maintenance Guide](./MAINTENANCE.md).

## Framework Interactions and Workarounds

### FastAPI and Pydantic

FastAPI leverages Pydantic extensively for request/response validation and serialization. Define clear Pydantic models in `api/models.py` for robust API contracts.

### PydanticAI and LLMs

PydanticAI agents use Pydantic models (`agents/` or `models/`) to structure prompts and parse LLM responses, ensuring predictable outputs.

### FastMCP Tool Parameter Types

We encountered an issue where the FastMCP framework had difficulty registering tool parameters defined with complex optional types like `Optional[Dict[str, Any]]` or even `Optional[str]`, resulting in "type undefined" errors even after server restarts.

The successful workaround was to define the problematic parameter (`config` in the MCP tool) as a **non-optional dictionary with a default empty value**: `config: Dict[str, Any] = {}`.

Inside the tool function, we check if the received `config` dictionary is non-empty before attempting to parse it into the corresponding Pydantic model (`LinterConfig`). If the client doesn't provide the `config` parameter in the tool call, it correctly defaults to the empty dictionary `{}`.

This approach satisfies the framework's apparent requirement for simpler, non-optional type hints in the tool signature while still allowing optional configuration data to be passed and validated internally using Pydantic.

## Conversation Management Subsystem (In Progress)

A new subsystem enables persistent, multi-turn conversations with the AI assistant:

- The Minecraft mod issues explicit commands (e.g., `/ai chat new`, `/ai chat list`, `/ai <message>`).
- These commands call FastAPI endpoints (`/chats`, `/chats/{conversation_id}/messages`).
- The backend stores conversation and message data in the SQLModel-powered database.
- When a message is added, the full conversation history is passed to the PydanticAI agent for context-aware replies.

This design keeps DB, API, and mod logic modular, making it easy to extend with features like public conversations or invites. See [wishlist/conversation-history.md](../wishlist/conversation-history.md) for the evolving design and requirements.
