# Cursor Rules Guide

This document describes the Cursor rules set up for this project and how to get the most out of your AI-assisted development workflow.

## Introduction

[Cursor](https://cursor.sh/) is an AI-powered code editor that enhances developer productivity. This project includes custom rules to maximize the benefits of AI assistance while maintaining code quality and documentation standards.

## Getting Started with Cursor

1. **Install Cursor**: Download from [cursor.sh](https://cursor.sh/)
2. **Open the Project**: Open the project folder in Cursor
3. **Verify Rules**: The rules should be automatically loaded from `.cursor/rules.yml`

## Using @ Symbols for Context

Cursor supports @ symbols for referencing files, docs, and code in chats:

- `@file.py`: Reference a file
- `@docs/OVERVIEW.md`: Reference documentation
- `@src/minecraft_ai/api/models.py:10-20`: Reference specific code lines

### Keyboard Shortcuts

- Type `@` in chat to see suggestions
- Use arrow keys to navigate suggestions
- Hit `Enter` to select

## Rule Categories

### 1. Documentation-First Rules

These rules remind you to update documentation when you modify code. They help maintain the documentation and code in sync.

### 2. Type Safety Enforcement

These rules ensure strong typing is maintained throughout the codebase, which is essential for PydanticAI's functionality.

### 3. MCP Tool Validation

When working with Model Context Protocol (MCP), these rules ensure you follow best practices for tool development.

### 4. Pydantic Model Standards

These rules remind you of best practices when creating or modifying Pydantic models.

### 5. Test Coverage Guardian

These rules remind you to update tests when you modify code.

### 6. Accessibility Champion

These rules promote accessibility in user-facing components.

## Best Practices for AI Coding with Cursor

### Prompt Structure for PydanticAI

When asking Cursor to modify PydanticAI code, structure your prompts as:

1. **Location**: Specify where the change should happen
2. **Action**: Use clear action words (CREATE, UPDATE, ADD, etc.)
3. **Detail**: Provide specifics of what should change

Example:

```text
UPDATE src/minecraft_ai/api/models.py:
ADD field publication_date to StoryIdea model
Make it Optional[datetime] with ISO format validation
```

### Using the MCP Server

For MCP server development, include relevant context:

```text
@src/minecraft_ai/mcp_server.py

Add a new tool that provides text summarization
```

### Documentation References

Reference documentation for context:

```text
@docs/MODELS.md

Update the ProductRecommendation model based on these patterns
```

## Creating Custom Rules

To create additional Cursor rules:

1. Navigate to `.cursor/rules.yml`
2. Add new rules following the existing pattern
3. Restart Cursor to apply changes

## Troubleshooting

- If rules aren't activating, check that `.cursor/rules.yml` is properly formatted
- For reference issues, ensure paths are correct
- For large codebases, use `.cursorignore` to exclude irrelevant files

## Resources

- [Cursor Documentation](https://docs.cursor.com/)
- [Cursor's Model Context Protocol](https://docs.cursor.com/context/model-context-protocol)
- [Cursor Rules Reference](https://docs.cursor.com/context/rules-for-ai)

## Rule File Structure and Management

Each rule is defined in its own `.mdc` file within the `.cursor/rules/` directory.

### File Format

Rule files (`.mdc`) use Markdown with YAML frontmatter:

```yaml
---
description: "A brief explanation of when this rule applies (used by AI)"
globs: # List of glob patterns for files/folders
  - "src/minecraft_ai/**.py"
  - "!tests/**" # Optional negation
alwaysApply: false # Set to true for rules that always apply
---
# Rule Title (Optional)

Markdown content explaining the rule, best practices, links to relevant docs (@docs/...), etc.

This content is provided to the AI when the rule is triggered.
```

### Managing Rule Files (Recommended Workflow)

Directly editing `.mdc` files within the `.cursor/rules` directory while Cursor is active can sometimes lead to unexpected behavior or saving issues. To avoid this, use the provided helper script:

1. **Create/Edit in Staging**: Create or edit your rule files within the `.cursor/rules_staging/` directory using the `.md` extension (e.g., `.cursor/rules_staging/my-new-rule.md`). Ensure the YAML frontmatter is correct.
2. **Run the Script**: Open your terminal in the project root and run:

   ```bash
   # Make executable (only need to do this once)
   chmod +x scripts/tasks/move_rules.sh

   # Execute the script (or use 'make rules')
   ./scripts/tasks/move_rules.sh
   ```

3. **Verification**: The script moves the `.md` files to `.cursor/rules/`, renames them to `.mdc`, and removes the `.cursor/rules_staging` directory. The rules should now be active in Cursor.

This workflow ensures files are processed correctly without potential editor conflicts. The `.cursor/rules_staging` directory is ignored by Git.

## Example Rules Breakdown

Let's look at how a rule file (`.cursor/rules/tdd-guidance.mdc`) works:

```yaml
key: "tdd-guidance" # Unique identifier
trigger: # Conditions for showing the rule
  glob: "**/tests/**.py" # Show for files in the tests directory
```

This rule triggers when you open a Python file within the `tests/` directory.

### Rule Content Example

```markdown
## Test-Driven Development (TDD) Guidance

Remember our TDD workflow:
1. Write a failing test (`tests/`).
2. Implement the minimal code in `src/` to make it pass.
3. Refactor and add documentation (`README.md`, `docs/`).
```

## Rule Management Script (`make rules`)

The script `./scripts/tasks/move_rules.sh` handles moving rules from staging to the active directory:

1. Creates `.cursor/rules/` if it doesn't exist.
2. Moves files from `.cursor/rules_staging/*.md` to `.cursor/rules/`.
3. Renames them to `.mdc`.

   ```bash
   #!/bin/bash
   set -e # Exit on error

   SOURCE_DIR=".cursor/rules_staging"
   TARGET_DIR=".cursor/rules"

   # ... script content ...
   ```

4. Removes the staging directory if empty.

This workflow prevents editor conflicts when modifying rules directly in `.cursor/rules/`.
