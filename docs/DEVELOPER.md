# Developer Guide

This guide provides detailed setup instructions and development workflows for the PydanticAI API Template.

## Setting Up Your Development Environment

### Recommended: VS Code / Cursor with Dev Containers

This provides the most seamless experience:

1. Install the prerequisites:
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - [VS Code](https://code.visualstudio.com/) or [Cursor](https://cursor.sh/)
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   - A [Nerd Font](https://www.nerdfonts.com/) for terminal icons (optional but recommended)

2. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/pydanticai-api-template.git
   cd pydanticai-api-template
   ```

3. Open in VS Code/Cursor:

   ```bash
   code .  # Or open using the editor's UI
   ```

4. When prompted, click "Reopen in Container" or use the Command Palette:

   ```text
   Dev Containers: Reopen in Container
   ```

5. After the container builds (may take a few minutes the first time), you'll see a welcome message with available commands.

### Development Workflow

Once the dev container is running:

1. **Start the server:**
   - Type `start` in the terminal, or
   - Press `Cmd+Shift+B` (macOS) or `Ctrl+Shift+B` (Windows/Linux), or
   - Use VS Code's tasks menu

2. **Access the API:**
   - API documentation: <http://localhost:8000/docs>
   - ReDoc: <http://localhost:8000/redoc>

3. **Run common tasks:**
   - `lint` - Check code quality
   - `test` - Run tests
   - `validate` - Verify environment
   - `sync` - Sync configurations
   - `help` - Show all available commands

4. **Debugging:**
   - Open the Debug panel in VS Code/Cursor
   - Select "FastAPI: Debug Server" configuration
   - Press F5 to start debugging

5. **Using the Wishlist:**
   - Browse `wishlist/` directory to see planned improvements
   - Add new markdown files to propose features or improvements
   - Reference wishlist items when implementing features
   - Use wishlist items as AI-assisted implementation targets

## Environment Variables

Create a `.env` file in the project root to store your API keys and other configuration:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
# Add other environment variables as needed (e.g., LOGFIRE_TOKEN)
```

The application will load these variables automatically at runtime. Note that the status check command looks for environment variables directly, so it may show warnings even when your app is working correctly with the .env file.

## Project Structure

```text
src/
└── pydanticai_api_template/    # Main Python package
    ├── __init__.py             # Package marker, exports version
    ├── api/                    # API related modules
    │   ├── endpoints.py        # FastAPI endpoints/routes
    │   └── models.py           # Pydantic models for API requests/responses
    └── cli.py                  # Typer CLI application logic
```

## Common Development Tasks

### Adding a New Endpoint

1. Add your Pydantic models in `src/pydanticai_api_template/api/models.py`
2. Create your endpoint in `src/pydanticai_api_template/api/endpoints.py`
3. Test your endpoint using the interactive docs

### Adding a New CLI Command

1. Modify `src/pydanticai_api_template/cli.py`
2. Run `sync` to update VS Code tasks

### Updating Dependencies

1. Update `pyproject.toml`
2. Run `uv sync` to update the lock file
3. Run `sync` to keep configurations in sync

### Working with the Wishlist

The Wishlist directory provides a structured way to plan and implement future improvements:

1. **Viewing Wishlist Items:**
   - Browse the `wishlist/` directory to see existing ideas
   - Review items to understand planned enhancements

2. **Adding New Wishlist Items:**
   - Create a new markdown file in the `wishlist/` directory
   - Use descriptive filenames (e.g., `feature-name.md`)
   - Structure with clear headings and implementation details
   - Include accessibility considerations where relevant

3. **Implementing Wishlist Items:**
   - Select items from the wishlist for implementation
   - Use AI assistance to help implement complex features
   - Reference the wishlist item in commit messages
   - Move implemented features from wishlist to documentation

4. **Best Practices:**
   - Keep wishlist items focused and actionable
   - Include enough detail for future implementation
   - Consider dependencies and prerequisites
   - Update or remove items as the project evolves

## Type Safety and mypy Best Practices

**Why is mypy so strict?**

mypy brings static type checking to Python, a dynamic language. This is powerful for catching bugs early and improving maintainability, but it can feel verbose or "picky"—especially when working with dynamic libraries (like Pydantic, FastAPI, or LLM agents) or strict settings (e.g., `no-any-return`).

### Key Principles

- **Type safety at boundaries:** Use precise types for public APIs and at the edges of your system. Limit the use of `Any` to places where you truly can't know the type in advance (e.g., external API responses).
- **Explicit is better than implicit:** When mypy can't infer a type, use explicit type annotations or `cast()` to clarify your intent.
- **Contain dynamic code:** Use type-safe adapters or utility functions to convert dynamic results (like LLM outputs) into well-typed objects before returning them from functions.
- **Balance strictness and productivity:** It's okay to relax strictness (e.g., disable a specific mypy check for a file or function) if the cost of compliance outweighs the benefit. Always document why.

### Practical Tips for Using mypy

- **Use `cast()` at dynamic boundaries:** When you know the runtime type but mypy can't infer it, use `from typing import cast` and wrap your return value:

  ```python
  from typing import cast, Dict, Any
  return cast(Dict[str, Any], result)
  ```

  Add a comment explaining why the cast is safe.
- **Limit `Any` to the edges:** Avoid propagating `Any` through your codebase. Convert to a concrete type as soon as possible.
- **Document exceptions:** If you need to use `# type: ignore`, specify the error code and add a comment explaining why.
- **Relax strictness selectively:** If a check like `no-any-return` causes excessive boilerplate, consider disabling it for that file or function with a clear comment:

  ```python
  # mypy: disable-error-code=no-any-return
  ```

- **Test type boundaries:** Write tests for utility functions that convert dynamic data to typed models.

### Example: Type-Safe Adapter

```python
from typing import cast, Dict, Any

def safe_story_response(result: Any) -> Dict[str, Any]:
    if isinstance(result, StoryResponse):
        return result.model_dump()
    if isinstance(result, dict):
        return {"error": "Unexpected dict", "data": result}
    return {"error": "Unknown result type", "data_type": str(type(result))}
```

### When to Relax mypy Strictness

- When working with highly dynamic code (e.g., LLM outputs, plugin systems)
- In test code or glue code where type safety is less critical
- When a strict check causes more friction than value—always document the reason

### Summary

- mypy is a powerful tool for maintainability and reliability, but it requires a balance between strictness and productivity.
- Use type annotations, `cast`, and utility functions to keep your codebase type-safe and readable.
- Don't be afraid to relax strictness in well-documented cases where it improves developer experience.

## AI Development Tools

This project includes tools to streamline AI-assisted development workflows.

### Repomix Runner (VS Code Extension)

- **Purpose**: Easily bundle files or directories into a single text block for pasting into AI chat prompts, providing necessary context.
- **Integration**: The [Repomix Runner VS Code extension](https://marketplace.cursorapi.com/items?itemName=DorianMassoulier.repomix-runner) is automatically installed when you open this project in the Dev Container.
- **Usage**:
  - Open the **REPOMIX** custom view in the VS Code sidebar.
  - Select files or folders in the Explorer.
  - Click "Run Repomix on selection" in the REPOMIX view.
  - The bundled content will be copied to your clipboard, ready to be pasted into your AI assistant (like Cursor).
  - You can also create and manage reusable bundles for commonly referenced parts of the codebase.

### Repomix CLI Tool

- **Purpose**: Generate a comprehensive text representation of your project or specific parts of it, suitable for providing context to Large Language Models (LLMs).
- **Installation**: The `repomix` CLI tool is installed globally within the dev container via the `Dockerfile`.
- **Basic Usage**:
  - Open the integrated terminal in VS Code/Cursor (`Terminal > New Terminal`).
  - Navigate to the project root directory (`cd /app` if not already there).
  - Run the command:

      ```bash
      repomix
      ```

  - By default, this command reads `.gitignore` and `.repomixignore` (if present) to exclude files and generates an output file named `repomix_output.txt` in the current directory.
  - This output file contains the bundled code and project structure, which you can then copy and paste into your AI assistant.
- **Common Options**:
  - **Specify output file**: `repomix -o custom_output.md`
  - **Specify input directory/files**: `repomix src/ tests/` (bundles only `src/` and `tests/`)
  - **Include specific patterns**: `repomix -p "src/**/*.py" -p "*.md"` (uses glob patterns)
  - **Ignore additional patterns**: `repomix -i "**/__pycache__" -i "*.log"`
  - **Copy to clipboard instead of file**: `repomix -c`
  - **Use a specific configuration file**: `repomix --config path/to/repomix.config.json`
  - **See all options**: `repomix --help`
- **Sane Defaults & Configuration**: Repomix uses sensible defaults (like ignoring `node_modules`, `.git`, etc.). You can customize behavior further by creating a `repomix.config.json` file in the project root. See the official [Repomix documentation](https://github.com/yamadashy/repomix?tab=readme-ov-file#configuration) for details.
- **When to Use**: Use the CLI when you need more control over the bundling process than the VS Code extension provides, such as specifying complex include/exclude patterns, using configuration files, or integrating repomix into scripts.

### Codex CLI Editor

- **Purpose**: The [OpenAI Codex CLI](https://github.com/openai/codex#quickstart) provides AI-powered, in-terminal coding assistance.
- **Installation (host, optional):**
  ```bash
  npm install -g @openai/codex
  ```
- **Usage inside the dev container:**
  - `codex` → opens an interactive shell
  - `codex "explain this codebase to me"` → one-shot prompt
  - Pipe in a file path:
    ```bash
    codex src/pydanticai_api_template/api/endpoints.py
    ```
- **VS Code Task:**
  - Open Command Palette → "Run Task" → "Codex: Interactive"
- **API Key:**
  - The `OPENAI_API_KEY` environment variable is automatically passed into the dev container for Codex CLI usage. Add your key to your `.env` file as shown in the Environment Variables section.

### Using the CLI

The project includes a command-line interface powered by Typer.
