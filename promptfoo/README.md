# PromptFoo Testing

This directory contains the [PromptFoo](https://promptfoo.dev/) configuration for testing prompts in the Minecraft AI.

## Setup

1. Make sure you have the development dependencies installed:

   ```bash
   uv pip install -e ".[dev]"
   ```

2. Set up environment variables for API keys:

   ```bash
   # Copy and edit the .env file
   cp .env.example .env
   ```

## Running Tests

To run the prompt tests:

```bash
promptfoo eval
```

To view the results in a web UI:

```bash
promptfoo view
```

## Testing Structure

- `config.yaml`: Main configuration file for PromptFoo
- `prompts/`: Directory containing prompt templates
  - `chat.txt`: Template for the chat API
  - `story.txt`: Template for the story idea API

## Adding New Tests

1. Add new prompts to the `prompts/` directory
2. Update `config.yaml` to include the new prompts and test cases
3. Run `promptfoo eval` to test the new prompts

## CI Integration

Prompt tests can be integrated into the CI pipeline by adding a job to the GitHub Actions workflow. This ensures that prompt quality remains high across code changes.
