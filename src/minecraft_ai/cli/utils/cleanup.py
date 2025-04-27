#!/usr/bin/env python
"""
Cleanup Script

This script removes unwanted files and directories that might be created
during development or container startup.

Usage:
    python scripts/cleanup.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Get the absolute path of the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def run_shell_command(command: str, cwd: Path | None = None) -> None:
    """Run a shell command and print output/errors."""
    try:
        process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=cwd)
        if process.stdout:
            print(f"Output:\n{process.stdout.strip()}")
        if process.stderr:
            print(f"Errors:\n{process.stderr.strip()}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}", file=sys.stderr)
        if e.stdout:
            print(f"Stdout:\n{e.stdout.strip()}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error running command '{command}': {e}", file=sys.stderr)


def remove_invalid_dirs() -> None:
    """Remove directories with invalid names (like '*' wildcards)."""
    print("Checking for invalid directory names...")
    # List of problematic directory patterns to check and remove
    # These sometimes get created unintentionally, especially in container volume mounts
    problem_dirs = ["**", "@**", "*", "!(__pycache__)", "@!(__pycache__)"]

    for problem_dir in problem_dirs:
        problem_path = PROJECT_ROOT / problem_dir
        # Basic check to avoid deleting the entire root if pattern is just '*'
        is_problem_dir = str(problem_path.name) == problem_dir
        if is_problem_dir and problem_path.exists() and problem_path.is_dir():
            print(f"Found potentially invalid directory: {problem_path}")
            print(f"Attempting removal of {problem_path}...")
            # Try shell command first; it might handle busy resources better
            run_shell_command(f'rm -rf "{problem_path}"', cwd=PROJECT_ROOT)

            # If it still exists, try the Python method
            if problem_path.exists():
                try:
                    shutil.rmtree(problem_path)
                    print(f"Removed directory using Python: {problem_path}")
                except OSError as e:
                    print(
                        f"Error removing directory {problem_path} using Python: {e}",
                        file=sys.stderr,
                    )
            else:
                print(f"Removed directory using shell: {problem_path}")
        elif problem_path.exists():
            # Path exists but isn't a dir, or the pattern is more complex.
            # Avoid accidentally deleting files matching these patterns for now.
            pass


def clean_pycache() -> None:
    """Clean __pycache__ directories recursively."""
    print("Cleaning __pycache__ directories...")
    count = 0
    for root, dirs, _files in os.walk(PROJECT_ROOT, topdown=False):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                print(f"Removing {pycache_path}...")
                shutil.rmtree(pycache_path)
                count += 1
            except OSError as e:
                print(f"Error removing {pycache_path}: {e}", file=sys.stderr)
    print(f"Removed {count} __pycache__ directories.")


def remove_egg_info() -> None:
    """Remove .egg-info directories if present and in .gitignore."""
    print("Checking for .egg-info directories...")
    # Check if *.egg-info/ is in .gitignore
    gitignore_path = PROJECT_ROOT / ".gitignore"
    ignore_egg_info = False
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r") as f:
                if any("*.egg-info/" in line for line in f):
                    ignore_egg_info = True
        except OSError as e:
            print(f"Warning: Could not read .gitignore: {e}")

    if ignore_egg_info:
        count = 0
        for path in PROJECT_ROOT.glob("*.egg-info"):
            if path.is_dir():
                try:
                    print(f"Removing {path}...")
                    shutil.rmtree(path)
                    count += 1
                except OSError as e:
                    print(f"Error removing {path}: {e}", file=sys.stderr)
        if count > 0:
            print(f"Removed {count} .egg-info directories.")
        else:
            print(".egg-info directories are ignored and none were found.")
    else:
        print(".egg-info directories are not specified in .gitignore, skipping removal.")


def main() -> None:
    """Main cleanup function."""
    print(f"Running cleanup in project root: {PROJECT_ROOT}")

    # Remove problematic directories first as they might interfere
    remove_invalid_dirs()

    # Clean __pycache__ directories
    clean_pycache()

    # Remove .egg-info if present and ignored
    remove_egg_info()

    print("\nCleanup finished.")


if __name__ == "__main__":
    main()
