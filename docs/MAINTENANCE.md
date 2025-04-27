# Project Maintenance Guide

This document explains how the project's configuration files are structured, how they relate to each other, and how to maintain them when making changes.

## Dev Container Architecture

The development environment uses VS Code's Dev Containers to provide a consistent, isolated environment.

```text
┌─────────────────────────────────┐
│         Host Machine            │
│                                 │
│ ┌─────────┐     ┌─────────────┐ │
│ │ VS Code │     │ Git Config  │ │
│ │ Cursor  │     │ Credentials │ │
│ └────┬────┘     └──────┬──────┘ │
└──────┼────────────────┼─────────┘
       │                │
       ▼                ▼
┌──────────────────────────────────────────────┐
│              Docker Container                │
│                                              │
│ ┌──────────┐ ┌────────┐ ┌─────────────────┐ │
│ │ Python   │ │ Source │ │ Dev Tools       │ │
│ │ FastAPI  │ │ Code   │ │ • Zsh + Oh My   │ │
│ │ PydanticAI│ │ (mount)│ │ • Modern CLIs  │ │
│ └──────────┘ └────────┘ │ • Ruff/MyPy     │ │
│                         └─────────────────┘ │
│ ┌──────────────────────────────────────────┐│
│ │ VS Code Server                           ││
│ │ • Extensions                             ││
│ │ • Tasks, Debugging                       ││
│ │ • Terminal                               ││
│ └──────────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

### How It Works

1. **Configuration Flow**:
   - `.devcontainer/devcontainer.json` defines the container configuration
   - It references `docker-compose.yml` (specifically the `minecraft-ai-dev` service) for container creation
   - VS Code Server runs inside the container to provide IDE features
   - The container runs as a non-root user by default for better security.

2. **Volume Mounting**:
   - Source code from the host is mounted into the container
   - Host's Git configuration is mounted for seamless Git operations
   - Container-specific directories (.venv, **pycache**) stay in the container for performance

3. **Development Workflow**:
   - The container starts without automatically launching the application
   - The container uses a minimal `tail -f /dev/null` command to stay running
   - Container health checks verify system health without requiring the API to be running
   - When the container starts, a welcome message shows available commands
   - Developers manually start the server with `start` command or VS Code tasks (Cmd+Shift+B)
   - VS Code tasks provide easy access to common operations
   - Extensions handle linting, formatting, and debugging inside the container
   - Changes to the code on the host are immediately visible in the container

This architecture allows developers to work with local files while having consistent tooling and dependencies across all development setups. The separation between container startup and application startup ensures better stability and easier troubleshooting.

## Configuration File Hierarchy

The project uses several configuration files that work together to create a seamless developer experience:

1. **pyproject.toml** - Primary configuration file (dependencies, project metadata, tool configs)
2. **Makefile** - Universal command interface
3. **Docker** files (`Dockerfile`, `Dockerfile.dev`, `docker-compose.yml`)
   - Docker Compose profiles control which services run by default:
     - `minecraft-ai-dev` (dev profile) - Development environment
     - `minecraft-ai` (prod profile) - Production-like environment
4. **VS Code** configurations (`.devcontainer/devcontainer.json`, `.vscode/tasks.json`)
5. **Pre-commit** configuration (`.pre-commit-config.yaml`)

## Environment Variables and .env Files

The project supports loading environment variables from `.env` files placed in the project root. This allows developers to:

1. Keep sensitive data like API keys out of version control
2. Configure the application locally without modifying container settings
3. Override default settings when needed

The `.env` file is automatically loaded by the application at startup. Note that the environment status check tool directly checks the environment variables, so it may show warnings even when your app is working correctly with the .env file.

## Git Configuration in Dev Containers

The development container includes Git configuration from the host system to provide a seamless experience. The configuration in `docker-compose.yml` maps your host Git config and credentials into the container, eliminating the need to configure Git inside the container.

Git environment variables (GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL) are also passed from the host to the container if they are set. This ensures that Git commits made inside the container are attributed correctly.

If users experience Git credential issues, ensure they have configured Git on their host machine.

## Config Synchronization Tool

To help keep configuration files in sync, the project includes a config synchronization tool in `scripts/update_configs.py`. This tool:

1. Reads from `pyproject.toml` as the single source of truth
2. Updates related configuration files automatically

To use it:

```bash
# Using make
make sync-configs

# Or directly
python scripts/update_configs.py
```

This will:

- Update pre-commit hook versions from dev dependencies
- Generate VS Code tasks based on available CLI commands
- Keep configurations in sync

Run this tool whenever you make significant changes to dependencies or CLI commands.

## Maintenance Guidelines

### Adding New Dependencies

When adding new dependencies:

1. Update `pyproject.toml` first:

   ```bash
   # For regular dependencies
   uv add <package-name>

   # For dev dependencies
   uv add --dev <package-name>
   ```

2. Run the config sync tool:

   ```bash
   make sync-configs
   ```

3. Update Docker images if needed:

   ```bash
   # Rebuild Docker images with new dependencies
   docker compose build
   ```

### Adding/Changing CLI Commands

When modifying the CLI:

1. Update `src/minecraft_ai/cli.py` to add or modify commands
2. Update automated tests as needed
3. Run the config sync tool to update VS Code tasks:

   ```bash
   make sync-configs
   ```

4. If necessary, manually update:
   - Makefile commands
   - README.md documentation

### Maintaining the Wishlist

The wishlist directory requires periodic maintenance to remain useful:

1. **Regular Reviews:**
   - Review wishlist items quarterly to ensure they remain relevant
   - Archive or update items that are no longer aligned with project goals
   - Prioritize items to guide implementation planning

2. **Documentation Updates:**
   - When a wishlist item is implemented, move relevant documentation to the appropriate docs
   - Update the README.md to reflect newly implemented features
   - Remove the wishlist item once fully implemented

3. **Organization:**
   - Group related wishlist items in subdirectories when the list grows
   - Add a README.md to the wishlist directory to provide an overview of items
   - Consider adding tags or priority indicators to help with planning

4. **Version Control:**
   - Include the wishlist directory in version control
   - Track wishlist changes alongside code changes
   - Use wishlist items as references in issue tracking systems

5. **Accessibility:**
   - Ensure wishlist items include accessibility considerations
   - Document how proposed features impact different users
   - Maintain consistent formatting for better screen reader compatibility

### Updating Docker Configuration

When changing Docker setup:

1. Modify `Dockerfile` and/or `Dockerfile.dev`
2. Update `docker-compose.yml` if service configuration changes
3. Test both production and development containers
4. If changing mounted paths or environment variables, also update `.devcontainer/devcontainer.json`

### Updating VS Code Configuration

When enhancing VS Code experience:

1. Modify `.devcontainer/devcontainer.json` for container settings, extensions, etc.
2. Tasks will be updated automatically by the sync tool, but you can manually edit `.vscode/tasks.json` if needed
3. Consider adding helpful VS Code settings in `.vscode/settings.json`

### Modifying Linting/Formatting Rules

When changing code quality tools:

1. Update configurations in `pyproject.toml` (ruff, ruff format, mypy sections)
2. Run the config sync tool to update pre-commit hook versions:

   ```bash
   make sync-configs
   ```

3. Consider running linting on entire codebase after changes

### Updating Core Dependencies

When updating major dependencies like Python, FastAPI, or UV:

1. **Review Changelogs**: Check the official changelogs for breaking changes or important migration notes.
2. **Update `pyproject.toml`**: Modify the version constraints as needed (e.g., `python = ">=3.12"`). Use `uv add <package>@latest` or specify versions.
3. **Update `Dockerfile` / `.devcontainer`**: Ensure the base images (e.g., `python:3.12-slim`) or setup steps reflect the new versions.
4. **Run `uv sync`**: Update the `uv.lock` file.
5. **Run `make sync-configs`**: Update any related config files.
6. **Thorough Testing**: Run all tests (`make test`) and manually test key features, especially those related to the updated dependency.
7. **Update Documentation**: Note the new versions in `README.md` or relevant places if significant.

### Maintaining External Tool Versions

When using external tools like promptfoo (Node.js), maintain version consistency across:

- `pyproject.toml`: `promptfoo==0.1.0` in dev dependencies
- `Dockerfile.dev`: `npm install -g promptfoo@0.1.0`
- CI/CD configurations in your workflow files

When upgrading, update all occurrences simultaneously to prevent version conflicts.

## Dependency Graph

Here's how the configuration files depend on each other:

```text
pyproject.toml           # Primary source of truth for dependencies
    │
    ├── Dockerfile       # Uses dependencies from pyproject.toml
    │   └── CI/CD        # Production container used in CI/CD
    │
    ├── Dockerfile.dev   # Development container definition
    │   ├── docker-compose.yml       # Defines dev (`minecraft-ai-dev`) and prod services
    │   └── .devcontainer/devcontainer.json  # Uses the dev service from docker-compose.yml
    │
    ├── .pre-commit-config.yaml  # Should align with dev dependencies
    │   └── (updated by sync tool)
    │
    ├── Makefile         # Commands should match available CLI commands (pat)
    │
    └── .vscode/tasks.json  # Tasks should align with CLI commands (pat)
        └── (updated by sync tool)
```

## Adding New Development Tools

When adding new development tools:

1. Add as a dev dependency in `pyproject.toml`
2. Run `make sync-configs` to update related configs
3. Add tool configuration in `pyproject.toml` if supported
4. Update VS Code extensions in `.devcontainer/devcontainer.json` if there's a corresponding extension
5. Add helpful Make commands in `Makefile`
6. Document in README.md

## Troubleshooting

### Container-related Issues

If the CLI doesn't work in containers:

1. Verify the installation path in the Dockerfile or check if it's on PATH: `which pat`
2. Check Python path and installation: `python -m minecraft_ai.cli --help`
3. Debug with `docker compose exec minecraft-ai-dev which pat`
4. Get a shell in the container for deeper debugging: `docker compose exec minecraft-ai-dev zsh`

### Application Startup Issues

If the server doesn't start when expected:

1. Make sure you're running `start` or pressing Cmd+Shift+B to manually start the server
2. Check for errors in the terminal output
3. Verify that port 8000 is not in use by another application
4. Try running the server with debug output: `pat run --reload --log-level debug`

### VS Code Dev Container Issues

If VS Code dev containers don't work:

1. Check Docker installation and permissions
2. Verify Dev Containers extension is installed
3. Try rebuilding: Command Palette → "Dev Containers: Rebuild Container"
4. Check VS Code logs: Command Palette → "Developer: Show Logs"

### Make Command Issues

If Make commands fail:

1. Verify Make is installed: `make --version`
2. Check command formatting in Makefile
3. Run with verbose output: `make -v <command>`

## CI/CD Integration

For CI/CD integration:

1. Use the production Docker container as the environment
2. Run validation using `pat validate`
3. Run tests using your test framework of choice (e.g., `pytest`)
4. Use health checks to verify deployment

Example GitHub Actions workflow fragment:

```yaml
- uses: actions/checkout@v4
```

## Documentation Maintenance

Documentation should evolve alongside code to maintain accuracy and usefulness. Follow these guidelines for documentation maintenance:

### Documentation Structure

The project's documentation is organized as follows:

1. **README.md** - Project overview, quick start guide, and navigation hub
2. **docs/** - Detailed technical documentation for specific topics
   - ARCHITECTURE.md - System design and component relationships
   - API.md - API endpoint specifications
   - DEVELOPER.md - Development setup and workflows
   - MODELS.md - Pydantic model details and validation
   - TESTING.md - Testing strategies and examples
   - MAINTENANCE.md - This file, covering configuration and maintenance

### Documentation Update Guidelines

When making changes to the project, update the appropriate documentation:

| Change Type | Documentation to Update | Content to Include |
|-------------|-------------------------|-------------------|
| API endpoints | API.md | Endpoint paths, methods, parameters, responses, authentication requirements |
| Pydantic models | MODELS.md | Model structure, validation rules, example usage |
| Project structure | README.md | Updated project structure diagram |
| Architecture | ARCHITECTURE.md | Component diagrams, flow explanations |
| Dev workflow | DEVELOPER.md | Command examples, environment setup |
| Configuration | MAINTENANCE.md | Config file relationships, environment variables |
| CLI commands | DEVELOPER.md | Command syntax, parameters, examples |
| Testing strategy | TESTING.md | Test patterns, fixtures, mocking approaches |

### Documentation Principles

For high-quality, maintainable documentation:

1. **Be Concise**: Focus on clarity and brevity
2. **Use Examples**: Include practical code examples for complex concepts
3. **Maintain Accuracy**: Remove outdated information immediately
4. **Consider Accessibility**: Use clear formatting, alt text for images
5. **Standardize Formatting**: Use consistent Markdown styling
6. **Link Appropriately**: Cross-reference related documentation
7. **Update Comprehensively**: When changing one doc, check for impacts on others

### AI Assistant Documentation Guidelines

When using AI assistants to help with documentation:

1. Direct the AI to update specific documentation files when making changes
2. Request concise documentation that focuses on practical usage
3. Ask for examples that demonstrate real use cases
4. Ensure the AI maintains the existing documentation structure
5. Have the AI update the README.md when adding new documentation files

## Final Checklist for Updates

Before committing significant changes:

- [ ] Update `pyproject.toml` with new dependencies/configurations
- [ ] Run `make sync-configs` to update related configuration files
- [ ] Update Docker configurations if needed
- [ ] Verify dev container works with VS Code
- [ ] Test all Make commands
- [ ] Update documentation in README.md and docs/MAINTENANCE.md
- [ ] Run pre-commit hooks: `pre-commit run --all-files`
