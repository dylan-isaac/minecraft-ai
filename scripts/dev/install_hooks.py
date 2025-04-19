#!/usr/bin/env python
"""
Install custom Git hooks for the PydanticAI API Template project.
"""

import os
import sys
from pathlib import Path


def install_pre_commit_hook() -> bool:
    """Install a pre-commit hook that runs sync-configs when CLI files change."""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("Git hooks directory not found. Is this a Git repository?")
        return False

    hook_path = hooks_dir / "pre-commit"

    hook_content = """#!/bin/sh
# Auto-sync configs when CLI files change
if git diff --cached --name-only | grep -q "src/pydanticai_api_template/cli.py"; then
    echo "CLI file changed, syncing configs..."
    python scripts/tasks/update_configs.py
    git add .vscode/tasks.json .pre-commit-config.yaml
fi
"""

    # Create or update the hook
    with open(hook_path, "w") as f:
        f.write(hook_content)

    # Make executable
    os.chmod(hook_path, 0o755)
    print(f"✅ Installed pre-commit hook at {hook_path}")
    return True


if __name__ == "__main__":
    success = install_pre_commit_hook()
    sys.exit(0 if success else 1)
