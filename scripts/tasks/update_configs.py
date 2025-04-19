#!/usr/bin/env python
"""
Config Synchronization Tool

This script helps keep various configuration files in sync by reading from
pyproject.toml as the primary source of truth and updating related files like
.pre-commit-config.yaml and .vscode/tasks.json.

Usage:
    python scripts/update_configs.py

This will:
1. Read dependencies and CLI script name from pyproject.toml.
2. Update version numbers for relevant hooks in .pre-commit-config.yaml.
3. Generate/update VS Code tasks in .vscode/tasks.json based on available CLI commands.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Use tomli for TOML parsing (standard lib in 3.11+, included for <3.11)
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        print("Error: 'tomli' is required for Python < 3.11. Please install it.")
        sys.exit(1)

# Use PyYAML for YAML parsing
try:
    import yaml
except ImportError:
    print(
        "Error: 'PyYAML' is required for this script. "
        "Please install it ('uv pip install pyyaml')."
    )
    sys.exit(1)

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
PRECOMMIT_CONFIG_PATH = PROJECT_ROOT / ".pre-commit-config.yaml"
TASKS_JSON_PATH = PROJECT_ROOT / ".vscode" / "tasks.json"

# Map pyproject.toml dependency names to pre-commit repo URLs (add more as needed)
DEP_TO_PRECOMMIT_REPO = {
    "ruff": "https://github.com/astral-sh/ruff-pre-commit",
    "black": "https://github.com/psf/black",
    "mypy": "https://github.com/pre-commit/mirrors-mypy",
    # Add other mappings if you use more pre-commit hooks tied to specific dependencies
}

# Define the base structure for tasks.json if it doesn't exist
DEFAULT_TASKS_STRUCTURE = {"version": "2.0.0", "tasks": []}

# Define tasks based on assumed CLI commands (adjust if your CLI changes)
# We'll dynamically get the CLI script name from pyproject.toml
CLI_COMMANDS_FOR_TASKS = [
    {
        "label": "Run Dev Server",
        "command": "run",
        "args": ["--reload"],
        "group": "build",
        "isDefault": True,
    },
    {"label": "Lint", "command": "lint", "args": []},
    {"label": "Test", "command": "test", "args": []},
    {"label": "Validate Environment", "command": "validate", "args": []},
    # Assumes a make target:
    {"label": "Sync Configs", "command": "sync-configs", "args": []},
    # Example task:
    {"label": "Install Completion", "command": "install-completion", "args": []},
    # Example task:
    {"label": "Cleanup", "command": "cleanup", "args": []},
]

CONFIG_FILE = "pyproject.toml"
PROJECT_NAME = "pydanticai_api_template"
# Ignore type checking on non-literal assignment
IGNORE_TYPES = ["mcp"]


# --- Helper Functions ---


def read_pyproject() -> Tuple[Dict[str, Any], Optional[str]]:
    """Read pyproject.toml and extract relevant data."""
    print(f"Reading project config from: {PYPROJECT_PATH}")
    if not PYPROJECT_PATH.exists():
        print(f"Error: {PYPROJECT_PATH} not found!", file=sys.stderr)
        sys.exit(1)
    try:
        with open(PYPROJECT_PATH, "rb") as f:
            pyproject_data = tomllib.load(f)
        # Extract CLI script name
        cli_script_name = None
        scripts = pyproject_data.get("project", {}).get("scripts", {})
        if scripts:
            # Assuming the first script defined is the main CLI entry point
            cli_script_name = list(scripts.keys())[0]
            print(f"Detected CLI script name: {cli_script_name}")
        else:
            print("Warning: No [project.scripts] found in pyproject.toml.")

        return pyproject_data, cli_script_name
    except Exception as e:
        print(f"Error reading or parsing {PYPROJECT_PATH}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_dev_dependencies(pyproject_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract development dependency names and versions."""
    dev_deps: Dict[str, str] = {}
    optional_deps = pyproject_data.get("project", {}).get("optional-dependencies", {})
    dev_list = optional_deps.get("dev", [])

    for dep_str in dev_list:
        # Regex to capture package name and version specifier
        # Handles >=, ==, ~, ^ etc. and extracts the base version number
        pattern = (
            r"^([a-zA-Z0-9_-]+)"  # Package name
            r"\s*([>=<^~!]+)?"  # Optional version constraint operator
            r"\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:[a-zA-Z0-9.-]*)?)"  # Version
        )
        match = re.match(pattern, dep_str)
        if match:
            name, _, version = match.groups()
            dev_deps[name] = version
        else:
            # Handle cases without version specifiers, or just log a warning
            name_match = re.match(r"^([a-zA-Z0-9_-]+)", dep_str)
            if name_match:
                print(
                    f"Warning: Could not parse version for dev dependency '{dep_str}'. "
                    f"Adding without version."
                )
                dev_deps[name_match.group(1)] = ""  # Or some default/marker
            else:
                print(f"Warning: Could not parse dev dependency string '{dep_str}'")

    print(f"Found {len(dev_deps)} development dependencies.")
    return dev_deps


def update_precommit_config(dev_deps: Dict[str, str]) -> None:
    """Update .pre-commit-config.yaml with versions from dev dependencies."""
    print(f"Checking/Updating pre-commit config: {PRECOMMIT_CONFIG_PATH}")
    if not PRECOMMIT_CONFIG_PATH.exists():
        print("Warning: .pre-commit-config.yaml not found, skipping update.")
        return

    try:
        with open(PRECOMMIT_CONFIG_PATH, "r") as f:
            precommit_config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading or parsing {PRECOMMIT_CONFIG_PATH}: {e}", file=sys.stderr)
        return

    if not precommit_config or "repos" not in precommit_config:
        print("Warning: Invalid or empty .pre-commit-config.yaml, skipping update.")
        return

    updated = False
    for repo in precommit_config.get("repos", []):
        repo_url = repo.get("repo")
        current_rev = repo.get("rev")

        # Find which dev dependency maps to this repo
        mapped_dep_name: Optional[str] = None
        for dep_name, url in DEP_TO_PRECOMMIT_REPO.items():
            if repo_url == url:
                mapped_dep_name = dep_name
                break

        if mapped_dep_name and mapped_dep_name in dev_deps:
            target_version = dev_deps[mapped_dep_name]
            if target_version:
                # Attempt to format the version similarly, assuming semantic versioning
                # Basic check: add 'v' if it's missing and looks like X.Y.Z
                is_semver = re.match(r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$", target_version)
                if not target_version.startswith("v") and is_semver:
                    target_rev = f"v{target_version}"
                else:
                    # Use the version as-is if it has 'v' or other format
                    target_rev = target_version

                if current_rev != target_rev:
                    print(
                        f"  Updating repo '{repo_url}' rev from '{current_rev}' "
                        f"to '{target_rev}' (based on '{mapped_dep_name}' dependency)"
                    )
                    repo["rev"] = target_rev
                    updated = True
            else:
                print(
                    f"Warning: No version found for dependency '{mapped_dep_name}' "
                    f"to update repo '{repo_url}'"
                )

    if updated:
        try:
            with open(PRECOMMIT_CONFIG_PATH, "w") as f:
                yaml.dump(precommit_config, f, sort_keys=False, indent=2)
            print("Successfully updated .pre-commit-config.yaml.")
        except Exception as e:
            print(
                f"Error writing updated {PRECOMMIT_CONFIG_PATH}: {e}", file=sys.stderr
            )
    else:
        print(
            "No version updates needed for pre-commit hooks "
            "based on tracked dependencies."
        )


def generate_vscode_task(
    label: str,
    cli_script_name: str,
    command: str,
    args: List[str],
    group: Optional[str] = None,
    is_default: bool = False,
) -> Dict[str, Any]:
    """Generate a VS Code task dictionary using Make as the executor."""
    task: Dict[str, Any] = {
        "label": label,
        "type": "shell",
        # Use Make to run the command - ensures environment setup (like venv)
        # is handled if Make is configured
        "command": "make",
        "args": [command],  # Pass the Make target (maps to CLI command)
        "problemMatcher": [],
        "detail": f"Runs: make {command}",
    }
    if group:
        task["group"] = {"kind": group, "isDefault": is_default}
    # Add presentation options if desired
    # task["presentation"] = {
    #     "echo": True,
    #     "reveal": "always",
    #     "focus": False,
    #     "panel": "shared",
    #     "showReuseMessage": False,
    #     "clear": False
    # }
    return task


def update_vscode_tasks(pyproject: Dict[str, Any]) -> None:
    """Update VS Code tasks based on available CLI commands."""
    tasks_path = Path(".vscode/tasks.json")
    # Use project name from pyproject.toml
    project_name = pyproject.get("project", {}).get("name", "pydanticai-api-template")

    # Define base structure if file doesn't exist
    if not tasks_path.exists():
        # Ensure parent directory exists
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        tasks: Dict[str, Any] = {"version": "2.0.0", "tasks": []}
    else:
        try:
            with open(tasks_path) as f:
                # Use json.load for .json file
                tasks = json.load(f) or {"version": "2.0.0", "tasks": []}
        except (json.JSONDecodeError, FileNotFoundError):
            tasks = {"version": "2.0.0", "tasks": []}

    assert isinstance(tasks, dict), (
        f"Expected 'tasks' to be a dict, but got {type(tasks)}"
    )

    # Ensure tasks["tasks"] exists and is a list
    if "tasks" not in tasks or not isinstance(tasks["tasks"], list):
        tasks["tasks"] = []  # Initialize or reset if invalid type

    # Define tasks based on CLI commands - Use project_name variable
    # Ensure commands defined in cli.py exist
    cli_tasks: List[Dict[str, Any]] = [
        {
            "label": f"Run Dev Server ({project_name})",  # Use project_name
            "type": "shell",
            "command": f"{project_name} run --reload",  # Use project_name
            "group": {"kind": "build", "isDefault": True},
            "problemMatcher": [],
            "detail": "Runs the FastAPI server with hot reload using the CLI.",
            "presentation": {
                "reveal": "always",
                "panel": "dedicated",
                "clear": True,
            },
            "runOptions": {"runOn": "folderOpen"},
        },
        {
            "label": f"Lint ({project_name})",  # Use project_name
            "type": "shell",
            "command": "make lint",  # Keep using make lint for simplicity
            "group": "test",
            "problemMatcher": ["$ruff"],
            "detail": "Runs Ruff linter and formatter checks using Make.",
        },
        {
            "label": f"Test ({project_name})",  # Use project_name
            "type": "shell",
            "command": "make test",  # Keep using make test for simplicity
            "group": {"kind": "test", "isDefault": True},
            "problemMatcher": [],
            "detail": "Runs pytest using Make.",
        },
        {
            "label": f"Validate ({project_name})",  # Use project_name
            "type": "shell",
            "command": f"{project_name} validate",  # Use project_name
            "problemMatcher": [],
            "detail": "Runs the CLI validation command.",
        },
        {
            "label": f"Cleanup ({project_name})",  # Use project_name
            "type": "shell",
            "command": f"{project_name} cleanup",  # Use project_name
            "problemMatcher": [],
            "detail": "Runs the CLI cleanup command.",
        },
        {
            "label": f"Sync Configs ({project_name})",  # Use project_name
            "type": "shell",
            "command": "make sync-configs",  # Keep using make sync-configs
            "problemMatcher": [],
            "detail": "Runs the configuration synchronization script.",
        },
    ]

    # Remove existing CLI tasks before adding updated ones
    existing_labels = {task["label"] for task in cli_tasks}
    # Now safely access tasks["tasks"] because we ensured it's a list
    current_tasks = tasks["tasks"]
    tasks["tasks"] = [
        task
        for task in current_tasks  # Use the validated list
        # Ensure task is a dict before getting label
        if isinstance(task, dict) and task.get("label") not in existing_labels
    ]
    tasks["tasks"].extend(cli_tasks)

    # Write updated tasks using json.dump for .json file
    with open(tasks_path, "w") as f:
        json.dump(tasks, f, indent=4)
        f.write("\n")  # Add final newline for consistency

    print(f"Updated VS Code tasks in {tasks_path}")


# --- Main Execution ---


def main() -> None:
    """Main function to update all configs."""
    print("Starting config synchronization...")
    pyproject, cli_script_name = read_pyproject()
    dev_deps = extract_dev_dependencies(pyproject)
    update_precommit_config(dev_deps)
    update_vscode_tasks(pyproject)
    print("Config synchronization complete.")


if __name__ == "__main__":
    main()
