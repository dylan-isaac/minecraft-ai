# PydanticAI API Template

A modern Python project template for building AI-powered APIs with PydanticAI, FastAPI, and Docker.

## Quick Start (Recommended)

1. **Prerequisites**:
   - [VS Code](https://code.visualstudio.com/) or [Cursor](https://cursor.sh/)
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   - [Docker](https://www.docker.com/products/docker-desktop/)
   - A [Nerd Font](https://www.nerdfonts.com/) for optimal terminal experience (optional)

### Terminal Icons and Nerd Fonts

The development environment uses modern CLI tools like `eza` with icons enabled (`--icons`). For these icons to display correctly in the integrated terminal (VS Code / Cursor):

1. **Install a Nerd Font on your host machine** (not in the container).
    - The `.devcontainer/devcontainer.json` is configured to use **"MesloLGM Nerd Font Mono"** by default.
    - You can download this specific font or another Nerd Font variant (like Meslo, Fira Code, Hack) from the [Nerd Fonts website](https://www.nerdfonts.com/font-downloads). Make sure to get a "Nerd Font" version (often suffixed with `NF` or `Nerd Font`).
    - Install the downloaded font on your **host** operating system (e.g., through Font Book on macOS).

2. **Verify VS Code/Cursor Configuration**:
    - The Dev Container setting `terminal.integrated.fontFamily` in `.devcontainer/devcontainer.json` is set to `"MesloLGM Nerd Font Mono"`.
    - If you installed a *different* Nerd Font on your host, **update this setting** in `.devcontainer/devcontainer.json` to match the *exact name* of the font you installed *before* rebuilding the container. You can find the exact name in your OS's font manager (e.g., Font Book on macOS).

3. **Configure External Terminals (If Applicable)**:
    - If you use a terminal *outside* of VS Code/Cursor to interact with the container, ensure that terminal is also configured to use the Nerd Font you installed on your host.

**Note:** If you see boxes (`□`) or missing icons in the terminal after rebuilding the container, it likely means the font name specified in `.devcontainer/devcontainer.json` doesn't exactly match a Nerd Font installed and recognized on your host system. Double-check the font name in your OS font manager and the `devcontainer.json` setting.

1. **Open in Dev Container**:
   - Clone this repository
   - Open in VS Code/Cursor
   - Click "Reopen in Container" when prompted

2. **Start Development**:
   - Inside the container, run `start` or press `Cmd+Shift+B` (macOS) / `Ctrl+Shift+B` (Windows/Linux)
   - Visit <http://localhost:8000/docs> for API documentation
   - For the MCP server: `pat run-mcp` (accessible at <http://localhost:3001>)

## Documentation Map

This README provides a high-level overview. For detailed information, refer to:

| Documentation                                | Purpose                                                 |
| -------------------------------------------- | ------------------------------------------------------- |
| [Documentation Overview](./docs/OVERVIEW.md) | Comprehensive guide to all documentation                |
| [Developer Guide](./docs/DEVELOPER.md)       | Setup instructions and development workflows            |
| [Architecture](./docs/ARCHITECTURE.md)       | System design, patterns, and component relationships    |
| [Models](./docs/MODELS.md)                   | Pydantic models, validation, and PydanticAI integration |
| [API Reference](./docs/API.md)               | API endpoints, parameters, and response formats         |
| [Testing Guide](./docs/TESTING.md)           | Testing strategies and examples                         |
| [Maintenance](./docs/MAINTENANCE.md)         | Configuration management and project maintenance        |
| [Observability](./docs/OBSERVABILITY.md)     | Logging, tracing, and monitoring with Logfire           |
| [Cursor Rules](./docs/CURSOR_RULES.md)       | AI-assisted development with Cursor                     |
| [Wishlist](./wishlist/)                      | Future improvements and feature ideas                   |

## Key Features

- **PydanticAI**: Structured interactions with LLMs using Pydantic models
- **FastAPI**: High-performance API framework with automatic docs
- **MCP Server**: Model Context Protocol server for AI agent access
- **Type Safety**: End-to-end type checking with mypy and Pydantic
- **Docker**: Containerization for consistent development and deployment
- **Modern Tooling**: Ruff, MyPy, UV package manager, and more
- **Prompt Testing**: Automated testing for LLM prompts with CI/CD integration
- **Observability**: Complete visibility with Logfire integration
- **Cursor Rules**: Smart AI-assisted development with contextual reminders
- **Repomix Runner**: Easily bundle project files for providing context to AI assistants ([VS Code Extension](https://marketplace.cursorapi.com/items?itemName=DorianMassoulier.repomix-runner))

## Project Maintenance

Maintaining this project involves keeping dependencies up-to-date, synchronizing configuration files, and managing Docker environments. For detailed instructions on managing dependencies, CLI commands, Docker configurations, and more, please refer to the [Project Maintenance Guide](./docs/MAINTENANCE.md).

## AI-Assisted Development with Cursor

This project includes custom [Cursor Rules](./docs/CURSOR_RULES.md) to enhance your
development experience when using [Cursor](https://cursor.sh/), an AI-powered code
editor:

- **Documentation Reminders**: Get contextual reminders to update documentation when
  changing code
- **Type Safety Enforcement**: Maintain type safety throughout the codebase
- **Director Pattern Detection**: Identify opportunities for implementing autonomous AI
  workflows
- **Repomix Integration**: Use the [Repomix Runner extension](https://marketplace.cursorapi.com/items?itemName=DorianMassoulier.repomix-runner)
  (automatically installed in the dev container) to easily bundle files or directories
  and copy them to the clipboard for pasting into AI chat prompts.

To get started with the Cursor Rules:

1. Open the project in Cursor
2. The rules will be automatically loaded from `.cursor/rules.yml`
3. Start coding and benefit from smart, contextual assistance
4. Use `@` symbol references (e.g., `@docs/MODELS.md`) to bring relevant context into chats

For detailed information, see the [Cursor Rules Guide](./docs/CURSOR_RULES.md).

### Managing Cursor Rules

Due to potential editor interference when directly modifying files in the `.cursor/rules/` directory, a helper script is provided for a safer workflow:

1. **Create/Edit Rules**: Make your changes to rule files (or create new ones) with the `.md` extension inside the staging directory `.cursor/rules_staging/` at the project root. Ensure each file starts with the correct YAML frontmatter (see `docs/CURSOR_RULES.md` for structure).
2. **Run the Script**: Execute `make rules` or `./scripts/tasks/move_rules.sh` (make sure it's executable: `chmod +x scripts/tasks/move_rules.sh`).
3. **Result**: The script will move all `.md` files from `.cursor/rules_staging/` to `.cursor/rules/`, rename them with the `.mdc` extension, and remove the (now empty) `.cursor/rules_staging/` directory.

This ensures the files are correctly formatted and placed without potential conflicts during the editing process.

## Project Structure

```text
├── .cursor          # Cursor AI rules and configuration
├── .devcontainer    # Dev container configuration
├── .vscode          # VS Code settings and tasks
├── docs/            # Detailed documentation
├── promptfoo/       # Prompt testing configuration
├── src/             # Source code
│   └── pydanticai_api_template/
│       ├── api/     # FastAPI routes and endpoints
│       ├── agents/  # PydanticAI agent definitions
│       ├── models/  # Pydantic data models
│       ├── mcp/     # MCP server implementation
│       └── cli.py   # Command-line interface
├── tests/           # Test suite
├── wishlist/        # Future improvements and feature ideas
├── pyproject.toml   # Project dependencies and config
└── Makefile         # Common development commands
```

## Basic Usage Examples

### PydanticAI Structured Outputs

```python
from pydantic_ai import Agent
from pydantic import BaseModel

class StoryIdea(BaseModel):
    title: str
    premise: str

story_agent = Agent("openai:gpt-4o", result_type=StoryIdea)
result = await story_agent.run("Give me a sci-fi story idea")
```

### Story API Endpoint

You can generate story ideas using the `/story` endpoint:

```bash
cURL -X POST "http://localhost:8000/story" \\
  -H "Content-Type: application/json" \\
  -d '{"message":"Give me a sci-fi story about time travel"}'
```

Response:

```json
{
  "title": "Echoes of Tomorrow",
  "premise": "A physicist discovers that time isn't linear but layered, with each moment existing simultaneously. When she builds a device to view these layers, she witnesses a future catastrophe and must find a way to reach across time to prevent it."
}
```

### MCP Server Connection

Connect any MCP-compatible client to access tools:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

server = MCPServerHTTP(url='http://localhost:3001/sse')
agent = Agent('openai:gpt-4o', mcp_servers=[server])
```

## Codex CLI Editor

We bundle the [OpenAI Codex CLI](https://github.com/openai/codex#quickstart) into our dev container for AI-powered, in-terminal coding assistance.

**Install (on your host, if you ever need it locally):**
```bash
npm install -g @openai/codex
```

**Usage inside the container:**
- `codex` → opens an interactive shell
- `codex "explain this codebase to me"` → one-shot prompt
- You can also pipe in a file path:
  ```bash
  codex src/pydanticai_api_template/api/endpoints.py
  ```

**VS Code Task:**
- Open Command Palette → "Run Task" → "Codex: Interactive"

**API Key:**
- The `OPENAI_API_KEY` environment variable is automatically passed into the dev container for Codex CLI usage. Add your key to your `.env` file as shown in the Environment Setup section.

## Wishlist

The project includes a `wishlist/` directory for capturing future improvements and feature ideas. This serves as:

1. **Feature Backlog**: A place to document desired enhancements while focusing on current priorities
2. **AI-Driven Implementation**: Actionable items for AI to implement during coding sessions
3. **Collaborative Planning**: A way to track ideas from the entire team for future sprints

Current wishlist items:

- Templateizing and CookieCutter integration for project scaffolding

To contribute to the wishlist, add markdown files to the `wishlist/` directory with detailed descriptions of proposed features or improvements.

## Observability with Logfire

This template comes with built-in observability powered by Logfire. Key features include:

1. **Automatic Instrumentation** for FastAPI, PydanticAI, and HTTP requests
2. **Live Debugging** with real-time trace visualization
3. **LLM Call Monitoring** including prompts, tokens, and costs
4. **Performance Metrics** to identify bottlenecks

### Local Setup

```bash
# From inside the dev container
auth-logfire     # Authenticate with Logfire
use-logfire      # Set the current project
```

### Production Setup

Set these environment variables:

```dotenv
LOGFIRE_TOKEN="your-write-token"
LOGFIRE_ENABLED="true"
```

For detailed instructions, see [Observability](./docs/OBSERVABILITY.md).

## Environment Setup

Create a `.env` file in the project root with your API keys:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
PYDANTICAI_API_KEY=your_api_key_here  # For API authentication
```

### API Authentication

The API endpoints are protected with API key authentication. To generate a secure API key:

```bash
# Run the API key generation command
pat generate-api-key
```

This will generate a secure random key that you can add to your `.env` file as `PYDANTICAI_API_KEY`.

When making requests to protected endpoints like `/chat` or `/story`, include the API key in the `X-API-Key` header:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"message":"Tell me a joke"}'
```

If no API key is set in the environment, authentication will be skipped (with a warning in the logs).
