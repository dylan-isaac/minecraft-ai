"""Tests for the prompt_test CLI command."""

# Standard library imports
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import Mock, patch

# Third-party imports
import pytest
from typer.testing import CliRunner

# Local imports
from pydanticai_api_template.cli import app

runner = CliRunner()


@pytest.fixture
def mock_config_file(tmp_path: Path) -> str:
    """Create a temporary config file for testing."""
    config_dir = tmp_path / "promptfoo"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        """
prompts:
  - id: test
    label: Test Prompt
    raw: |
      Test prompt with {{input}}
providers:
  - id: test-provider
    config:
      temperature: 0
testCases:
  - description: Test case
    vars:
      input: "test input"
    assert:
      - type: javascript
        value: "true"
"""
    )
    return str(config_file)


@patch("dotenv.load_dotenv")
@patch("pydanticai_api_template.utils.observability.setup_logfire")
@patch("subprocess.run")
@patch("shutil.which")
def test_prompt_test_command(
    mock_which: Mock,
    mock_run: Mock,
    mock_setup_logfire: Mock,
    mock_load_dotenv: Mock,
    mock_config_file: str,
) -> None:
    """Test the prompt_test command with basic options."""
    # Set up mocks
    mock_which.return_value = "/usr/bin/npm"
    mock_run.return_value.returncode = 0

    # Run the command
    result = runner.invoke(app, ["prompt-test", "--config", mock_config_file])

    # Verify command executed successfully
    assert result.exit_code == 0

    # Verify logfire was set up
    mock_setup_logfire.assert_called_once_with(service_name="promptfoo-testing")

    # Verify dotenv was loaded
    mock_load_dotenv.assert_called_once()

    # Verify npm exec was called with correct arguments
    mock_run.assert_any_call(
        ["npm", "exec", "--", "promptfoo", "eval", "--config", mock_config_file],
        check=True,
        env=mock_run.call_args[1]["env"],
    )

    # Verify web UI was not opened
    assert not any("view" in str(call) for call in mock_run.call_args_list)


@patch("dotenv.load_dotenv")
@patch("pydanticai_api_template.utils.observability.setup_logfire")
@patch("subprocess.run")
@patch("shutil.which")
def test_prompt_test_with_view(
    mock_which: Mock,
    mock_run: Mock,
    mock_setup_logfire: Mock,
    mock_load_dotenv: Mock,
    mock_config_file: str,
) -> None:
    """Test the prompt_test command with view option."""
    # Set up mocks
    mock_which.return_value = "/usr/bin/npm"
    mock_run.return_value.returncode = 0

    # Run the command with view option
    result = runner.invoke(app, ["prompt-test", "--config", mock_config_file, "--view"])

    # Verify command executed successfully
    assert result.exit_code == 0

    # Verify web UI was opened
    assert any("view" in str(call) for call in mock_run.call_args_list)


@patch("dotenv.load_dotenv")
@patch("pydanticai_api_template.utils.observability.setup_logfire")
@patch("subprocess.run")
@patch("shutil.which")
def test_prompt_test_with_verbose(
    mock_which: Mock,
    mock_run: Mock,
    mock_setup_logfire: Mock,
    mock_load_dotenv: Mock,
    mock_config_file: str,
) -> None:
    """Test the prompt_test command with verbose option."""
    # Set up mocks
    mock_which.return_value = "/usr/bin/npm"
    mock_run.return_value.returncode = 0

    # Mock yaml module
    with patch("pydanticai_api_template.cli.yaml") as mock_yaml:
        mock_yaml.safe_load.return_value = {
            "prompts": [{"id": "test"}],
            "providers": [{"id": "test-provider"}],
            "testCases": [
                {"description": "Test case", "vars": {"input": "test"}, "assert": [{}]}
            ],
        }

        # Run the command with verbose option
        result = runner.invoke(
            app, ["prompt-test", "--config", mock_config_file, "--verbose"]
        )

    # Verify command executed successfully
    assert result.exit_code == 0

    # Verify verbose flag was passed to promptfoo
    mock_run.assert_any_call(
        [
            "npm",
            "exec",
            "--",
            "promptfoo",
            "eval",
            "--config",
            mock_config_file,
            "--verbose",
        ],
        check=True,
        env=mock_run.call_args[1]["env"],
    )


@patch("shutil.which")
def test_prompt_test_npm_not_found(mock_which: Mock, mock_config_file: str) -> None:
    """Test the prompt_test command when npm is not found."""
    # Set up mock to return None (npm not found)
    mock_which.return_value = None

    # Run the command
    result = runner.invoke(app, ["prompt-test", "--config", mock_config_file])

    # Verify command failed
    assert result.exit_code == 1
    assert "npm command not found" in result.stdout


@patch("shutil.which")
def test_prompt_test_config_not_found(mock_which: Mock) -> None:
    """Test the prompt_test command when config file is not found."""
    # Set up mock to return path to npm
    mock_which.return_value = "/usr/bin/npm"

    # Run the command with non-existent config file
    result = runner.invoke(app, ["prompt-test", "--config", "nonexistent.yaml"])

    # Verify command failed
    assert result.exit_code == 1
    assert "Config file not found" in result.stdout


@patch("dotenv.load_dotenv")
@patch("pydanticai_api_template.utils.observability.setup_logfire")
@patch("subprocess.run")
@patch("shutil.which")
def test_prompt_test_command_fails(
    mock_which: Mock,
    mock_run: Mock,
    mock_setup_logfire: Mock,
    mock_load_dotenv: Mock,
    mock_config_file: str,
) -> None:
    """Test the prompt_test command when the subprocess fails."""
    # Set up mocks
    mock_which.return_value = "/usr/bin/npm"

    # Make subprocess.run raise CalledProcessError
    mock_run.side_effect = CalledProcessError(1, "command")

    # Run the command
    result = runner.invoke(app, ["prompt-test", "--config", mock_config_file])

    # Verify command failed
    assert result.exit_code == 1
    assert "Prompt tests failed" in result.stdout
