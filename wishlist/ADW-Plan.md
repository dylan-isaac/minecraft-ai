# AI Developer Workflow (ADW) Scaffolding Tool Plan

## Overview

This document outlines the plan for creating an ADW scaffolding tool that will replace the existing AI workflow systems in the dotfiles repository. The new system will use PydanticAI for structured validation and Aider for code modifications, enabling an efficient, type-safe approach to automating development workflows.

## 1. Project Goals

- Replace the existing `ai-workflow` and `pai-workflow` commands with a unified, well-structured scaffolding system
- Create a command-line tool that can be installed globally using UV (Python package manager)
- Generate repository-specific AI workflows that maintain documentation and track changes
- Enable structured data validation and evaluation using PydanticAI
- Leverage Aider's Python API for intelligent code modifications
- Support MCP (Model Context Protocol) integration for connecting to external tools and data sources

## 2. System Architecture

```
adw-scaffold/
├── src/
│   └── adw_scaffold/
│       ├── __init__.py                 # Package initialization
│       ├── main.py                     # Entry point and CLI handling
│       ├── models/                     # Pydantic models
│       │   ├── requirements.py         # Models for workflow requirements
│       │   ├── workflow.py             # Models for workflow definitions
│       │   └── evaluation.py           # Models for testing and evaluation
│       ├── agents/                     # PydanticAI agent definitions
│       │   ├── requirements_agent.py   # Agent for gathering requirements
│       │   ├── scaffold_agent.py       # Agent for creating workflow scaffolds
│       │   └── evaluation_agent.py     # Agent for validating requirements
│       ├── templates/                  # Template workflows
│       │   ├── workflow_base.py        # Base template for workflows
│       │   ├── doc_workflow.py         # Documentation update template
│       │   ├── test_workflow.py        # Test validation template
│       │   └── spec_prompts/           # Template spec prompts
│       └── utils/                      # Utility functions
│           ├── git.py                  # Git operations
│           ├── file.py                 # File operations
│           └── aider.py                # Aider integration
├── pyproject.toml                      # Project dependencies
├── README.md                           # Documentation
└── tests/                              # Test suite
    ├── test_requirements.py            # Test requirements gathering
    ├── test_scaffold.py                # Test scaffold generation
    └── test_evaluation.py              # Test evaluation logic
```

## 3. Implementation Details

### 3.1 PydanticAI Models

The system will use Pydantic models for structured data validation:

```python
# models/requirements.py
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class FileAccessConfig(BaseModel):
    """Configuration for file access permissions."""
    path: str
    read: bool = True
    write: bool = False

class WorkflowStep(BaseModel):
    """A step in a workflow."""
    name: str
    description: str
    success_criteria: List[str]

class WorkflowDefinition(BaseModel):
    """Definition of a workflow."""
    name: str
    description: str
    trigger: str  # When this workflow should be triggered
    files_access: List[FileAccessConfig]
    steps: List[WorkflowStep]

class WorkflowRequirements(BaseModel):
    """Requirements for ADW scaffolding."""
    project_name: str
    project_description: str
    important_files: List[str]
    documentation_files: List[str]
    workflows: List[WorkflowDefinition]
```

### 3.2 Aider Integration

The system will use Aider's Python API for code modifications:

```python
# utils/aider.py
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

def setup_aider(model_name: str, editable_files: List[str], read_only_files: List[str] = None):
    """Set up an Aider coder instance."""
    io = InputOutput(yes=True)  # Auto-accept changes
    model = Model(model_name)

    return Coder.create(
        main_model=model,
        fnames=editable_files,
        read_only_fnames=read_only_files or [],
        io=io,
        auto_commits=False,  # Let the workflow decide when to commit
    )

def modify_code(coder: Coder, prompt: str) -> Dict:
    """Use Aider to modify code based on a prompt."""
    try:
        result = coder.run(prompt)
        return {
            "success": True,
            "message": "Code modified successfully",
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error modifying code: {str(e)}",
            "error": str(e)
        }
```

### 3.3 CLI Implementation

The main CLI will be implemented using Typer:

```python
# main.py
import os
import sys
from pathlib import Path
import typer
from rich import print
from typing import Optional

from .agents.requirements_agent import create_requirements_agent
from .agents.scaffold_agent import create_scaffold_agent

app = typer.Typer()

@app.command()
def init(
    context_dir: Optional[Path] = typer.Option(
        None, "--context", "-c", help="Directory to search for context"
    ),
    model: str = typer.Option(
        "gpt-4o", "--model", "-m", help="AI model to use"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for the workflows"
    ),
):
    """
    Initialize an AI Developer Workflow in the current repository.
    Starts a conversation to gather requirements and scaffold the ADW.
    """
    # Check if we're in a git repository
    if not Path(".git").exists():
        print("[bold red]Error:[/bold red] Not in a git repository.")
        sys.exit(1)

    # Default output directory is .adw in the current repo
    if not output_dir:
        output_dir = Path(".adw")

    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    # Get repository info
    repo_name = os.path.basename(os.getcwd())
    print(f"[bold green]Initializing ADW scaffolding for repository:[/bold green] {repo_name}")

    # Start conversation to gather requirements
    print("\n[bold]Starting requirements gathering conversation...[/bold]")
    requirements = gather_requirements(model, context_dir)

    # Create ADW scaffold based on requirements
    create_adw_scaffold(requirements, output_dir, model)

    print("\n[bold green]ADW scaffolding complete![/bold green]")
```

### 3.4 Model Context Protocol (MCP) Integration

The scaffolding system will incorporate MCP principles for connecting to external tools and data sources:

```python
# utils/mcp.py
from typing import Dict, Any, Optional
import requests
from pydantic import BaseModel

class MCPConnection(BaseModel):
    """Model Context Protocol connection configuration."""
    name: str
    endpoint: str
    auth_token: Optional[str] = None
    parameters: Dict[str, Any] = {}

class MCPTool:
    """A tool that connects to an MCP server."""
    def __init__(self, connection: MCPConnection):
        self.connection = connection

    def query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a query to the MCP server."""
        headers = {}
        if self.connection.auth_token:
            headers["Authorization"] = f"Bearer {self.connection.auth_token}"

        response = requests.post(
            self.connection.endpoint,
            json=payload,
            headers=headers
        )

        return response.json()
```

## 4. Example Workflow Template: Documentation Updater

```python
# templates/doc_workflow.py
from pathlib import Path
from aider.coders import Coder
from aider.models import Model
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List, Dict, Optional
import subprocess
import difflib

class DocUpdateRequirement(BaseModel):
    """Requirement for documentation update."""
    file_path: str
    change_description: str
    needs_update: bool

class FileChange(BaseModel):
    """Represents a change in a file between branches."""
    file_path: str
    is_added: bool = False
    is_modified: bool = False
    is_deleted: bool = False
    diff: Optional[str] = None

class DocUpdateResult(BaseModel):
    """Result of documentation update check."""
    updates_needed: List[DocUpdateRequirement]
    all_docs_updated: bool

def run_workflow():
    """
    Check if documentation is up-to-date with code changes between current branch and main.
    If not, update the documentation to reflect the changes.
    """
    print("Running Documentation Update workflow")

    # Setup files access
    editable_files = ["README.md", "CHANGELOG.md", "docs/"]
    read_only_files = ["src/", "tests/"]

    # Initialize the model
    model = Model("claude-3-5-sonnet-20241022")

    # Initialize the coder
    coder = Coder.create(
        main_model=model,
        fnames=editable_files,
        read_only_fnames=read_only_files,
        auto_commits=False,
    )

    # Get the current branch name
    current_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        universal_newlines=True
    ).strip()

    # Get file changes between current branch and main
    changes = get_branch_changes("main", current_branch)

    # Identify documentation that needs updating
    update_requirements = check_documentation_needs(changes)

    if not update_requirements.updates_needed:
        print("✅ All documentation is up-to-date!")
        return DocUpdateResult(updates_needed=[], all_docs_updated=True)

    # Update documentation using Aider
    update_results = update_documentation(coder, update_requirements.updates_needed)

    # Update CHANGELOG.md
    update_changelog(coder, update_requirements.updates_needed)

    return DocUpdateResult(
        updates_needed=update_requirements.updates_needed,
        all_docs_updated=all(update.get('success', False) for update in update_results)
    )

# Helper functions would be implemented here
```

## 5. UV Package Configuration

The tool will be packaged using UV for efficient distribution:

```toml
# pyproject.toml
[project]
name = "adw-scaffold"
version = "0.1.0"
description = "AI Developer Workflow Scaffolding Tool"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0.0",
    "pydantic-ai>=0.0.31",
    "aider>=0.25.0",
    "typer>=0.9.0",
    "rich>=13.4.2",
]

[project.scripts]
adw-scaffold = "adw_scaffold.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 6. Integration with Dotfiles

The tool will be integrated into the dotfiles repository:

1. Add the `adw-scaffold` command to the PATH
2. Create symlinks in the dotfiles/bin directory
3. Update documentation to reflect the new system
4. Remove old `ai-workflow` and `pai-workflow` commands

## 7. Implementation Plan

1. **Phase 1: Core Framework**
   - Implement basic project structure
   - Create core Pydantic models
   - Implement CLI command structure

2. **Phase 2: PydanticAI Integration**
   - Implement agents for requirements gathering
   - Create scaffold generation logic
   - Add evaluation system

3. **Phase 3: Aider Integration**
   - Implement code modification utilities
   - Create file access management
   - Add Git integration

4. **Phase 4: Workflow Templates**
   - Implement documentation updater
   - Create test validator
   - Add change tracker

5. **Phase 5: Packaging and Distribution**
   - Configure UV packaging
   - Create installation scripts
   - Update dotfiles integration

## 8. Testing Strategy

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test complete workflows

## 9. Documentation

1. **API Documentation**: Document all public APIs
2. **Usage Guide**: Create comprehensive usage instructions
3. **Example Workflows**: Provide examples for common use cases

## 10. Requirements and Dependencies

### 10.1 PydanticAI Requirements

- PydanticAI >= 0.0.31
- Structured data validation
- Agent-based architecture
- Tool definitions with proper typing
- Dependency injection for workflow contexts
- Result validation

### 10.2 Aider Requirements

- Aider Python API for code modifications
- Repository map for understanding code structure
- File access controls for safety
- Git integration

### 10.3 MCP Integration

- Connect to external tools and data sources
- Standardized protocol for data exchange
- Secure authentication

## Conclusion

The ADW Scaffolding Tool will provide a powerful, flexible system for creating and managing AI-driven development workflows. By combining PydanticAI's structured validation with Aider's code modification capabilities, the system will enable developers to automate routine tasks, maintain documentation, and ensure consistent code quality.
