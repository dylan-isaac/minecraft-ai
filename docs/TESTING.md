# Testing Guide

This document describes how to test the PydanticAI API Template, including the MCP server, model validation, and type checking.

## Running Tests

### Automated Tests

To run the automated tests:

```bash
# Run all tests
pat test

# Run specific tests with pytest directly
python -m pytest tests/test_mcp_server.py -v
```

### Test Coverage

To generate test coverage reports locally:

```bash
python -m pytest --cov=pydanticai_api_template tests/
```

This will show coverage statistics in the terminal output. You can also generate an HTML report for more detailed information:

```bash
python -m pytest --cov=pydanticai_api_template tests/ --cov-report=html
```

The HTML report will be generated in the `htmlcov/` directory.

## Testing the MCP Server

### MCP Server Automated Tests

The MCP server has unit tests in `tests/test_mcp_server.py` that test:

1. Server creation
2. Chat tool functionality
3. Error handling

### Manual Testing

#### Prerequisites

1. Install dependencies:

   ```bash
   pip install -e ".[test]"
   ```

2. Set up environment variables:

   ```bash
   # Create a .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

#### Running the MCP Server

Start the MCP server:

```bash
pat run-mcp
```

The server will start on <http://localhost:3001> by default.

#### Using the Example Client

Run the example MCP client to test connection to the server:

```bash
python examples/mcp_client_example.py
```

This will send test messages to the MCP server and display the responses.

#### Testing with curl

You can also test the SSE connection using curl:

```bash
curl -N http://localhost:3001/sse
```

This should establish a connection to the SSE endpoint.

## Testing Pydantic Models

### Writing Model Tests

Testing Pydantic models is crucial for ensuring your validation logic works correctly. Here's how to write effective tests:

```python
import pytest
from pydantic import ValidationError

from pydanticai_api_template.api.models import ChatMessage

def test_chat_message_valid():
    # Valid case
    msg = ChatMessage(message="Hello, how are you?")
    assert msg.message == "Hello, how are you?"

def test_chat_message_empty():
    # Empty message should fail validation
    with pytest.raises(ValidationError) as exc_info:
        ChatMessage(message="")

    # Check specific validation error details
    errors = exc_info.value.errors()
    assert any("empty" in str(err["msg"]) for err in errors)

def test_chat_message_whitespace():
    # Whitespace-only message should fail validation
    with pytest.raises(ValidationError) as exc_info:
        ChatMessage(message="   ")

    # Check specific validation error details
    errors = exc_info.value.errors()
    assert any("empty" in str(err["msg"]) for err in errors)
```

### Testing Complex Validation Rules

For models with interdependent validation rules, test each case:

```python
from pydanticai_api_template.api.models import UserSignup

def test_password_match():
    # Passwords match
    user = UserSignup(
        username="testuser",
        password="secureP@ss123",
        password_confirm="secureP@ss123"
    )
    assert user.password == user.password_confirm

def test_password_mismatch():
    # Passwords don't match
    with pytest.raises(ValidationError) as exc_info:
        UserSignup(
            username="testuser",
            password="secureP@ss123",
            password_confirm="differentP@ss"
        )

    errors = exc_info.value.errors()
    assert any("match" in str(err["msg"]) for err in errors)
```

### Testing JSON Serialization

Test that your models serialize to and from JSON correctly:

```python
import json
from pydanticai_api_template.api.models import ChatResponse

def test_chat_response_serialization():
    # Create model instance
    response = ChatResponse(reply="This is a test response")

    # Serialize to JSON
    json_str = response.model_dump_json()

    # Parse JSON back to Python
    data = json.loads(json_str)

    # Check data structure
    assert data == {"reply": "This is a test response"}

    # Recreate model from JSON
    new_response = ChatResponse.model_validate(data)
    assert new_response.reply == response.reply
```

## Mocking AI Services

Testing AI-powered applications can be challenging due to the need for API keys and the non-deterministic nature of AI responses. Here are effective mocking strategies:

### Mocking PydanticAI Agent

```python
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from pydanticai_api_template.api.models import ChatResponse
from pydanticai_api_template.api.endpoints import chat_with_agent

@pytest.mark.asyncio
@patch("pydanticai_api_template.api.endpoints.ai_agent")
async def test_chat_endpoint(mock_agent):
    # Create a mock result
    mock_result = MagicMock()
    mock_result.data = ChatResponse(reply="This is a mocked AI response")

    # Set up the mock to return our prepared result
    mock_agent.run = AsyncMock(return_value=mock_result)

    # Test the endpoint with a chat message
    from pydanticai_api_template.api.models import ChatMessage
    response = await chat_with_agent(ChatMessage(message="Hello AI"))

    # Verify the response
    assert response.reply == "This is a mocked AI response"

    # Verify the agent was called correctly
    mock_agent.run.assert_called_once_with("Hello AI")
```

### Testing Error Scenarios

```python
@pytest.mark.asyncio
@patch("pydanticai_api_template.api.endpoints.ai_agent", None)
async def test_chat_endpoint_no_agent():
    # Test when AI agent is not available
    from pydanticai_api_template.api.models import ChatMessage
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await chat_with_agent(ChatMessage(message="Hello AI"))

    # Verify status code and error message
    assert exc_info.value.status_code == 503
    assert "AI service is not available" in str(exc_info.value.detail)
```

## Type Checking Tests

Static type checking is an important part of the testing strategy. The project uses mypy for this purpose.

### Running Type Checks

```bash
# Check all files
mypy src tests

# Check specific modules
mypy src/pydanticai_api_template/api/models.py
```

### Common Type Issues and Solutions

1. **Untyped decorators**: Add specific module overrides in pyproject.toml:

   ```toml
   [[tool.mypy.overrides]]
   module = "pydanticai_api_template.api.models"
   disallow_untyped_decorators = false
   ```

2. **Missing return types**: Always add return types to functions:

   ```python
   def process_data(data: dict) -> dict:  # Add return type
       # Function implementation
       return processed_data
   ```

3. **Optional values**: Use `Optional` for values that might be None:

   ```python
   from typing import Optional

   def find_user(user_id: str) -> Optional[User]:
       # Implementation
       if not found:
           return None
       return user
   ```

## Type Checking Philosophy and mypy Best Practices

For a detailed discussion of mypy's philosophy, strictness, and best practices for type safety in this project, see:

👉 [Type Safety and mypy Best Practices](./DEVELOPER.md#type-safety-and-mypy-best-practices)

This section covers:

- Why mypy is strict and how to balance strictness with productivity
- Practical tips for using `cast`, limiting `Any`, and documenting exceptions
- When and how to relax strictness (with examples)
- Type-safe adapter patterns for dynamic results

## Testing Checklist

- [ ] Unit tests for all models
- [ ] Validation tests for model constraints
- [ ] API endpoint tests with mocked dependencies
- [ ] MCP server functionality tests
- [ ] Type consistency checks with mypy
- [ ] Error handling and edge case tests
- [ ] Accessibility compliance tests
- [ ] Test for race conditions in async code
- [ ] Verify that the MCP server starts without errors
- [ ] Verify that the chat tool responds to messages
- [ ] Verify error handling when the OpenAI API key is missing
- [ ] Verify error handling when the LLM service returns an error
- [ ] Verify that multiple clients can connect to the server

## Troubleshooting

### Common Issues

1. **"Module not found" errors**:
   - Make sure you've installed the package with dev dependencies: `pip install -e ".[dev,test]"`

2. **OpenAI API Key issues**:
   - Check that your OpenAI API key is correctly set in the .env file
   - Check that the .env file is in the correct location (project root)

3. **Port already in use**:
   - If port 3001 is already in use, change the port: `pat run-mcp --port 3002`

4. **Type checking errors**:
   - Check the function signatures and return types
   - Verify imported types are correct
   - Use `# type: ignore` sparingly and with specific error codes

### MCP Server Logs

To see detailed logs from the MCP server:

```bash
pat run-mcp --log-level debug
```

This will show more detailed information about the server operation and any errors.

## CI/CD Integration

When integrating tests with CI/CD pipelines, you can automate the verification of your API, MCP server, and prompts.

### Standard Testing

For basic API and MCP server testing:

```yaml
# Example GitHub Actions step
- name: Run Tests
  run: python -m pytest
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

# Type checking
- name: Type Check
  run: mypy src tests
```

### Prompt Testing in CI

Add prompt testing to your CI pipeline:

```yaml
# For GitHub Actions
- name: Setup Node.js and Python
  uses: actions/setup-node@v3 # For promptfoo
  with:
    node-version: '18'
- name: Install promptfoo
  run: npm install -g promptfoo@0.1.0
- name: Run prompt tests
  run: python -m pydanticai_api_template.cli prompt-test
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

```yaml
# For GitLab CI
prompt-testing:
  stage: test
  image: node:18
  before_script:
    - apt-get update && apt-get install -y python3 python3-pip
    - npm install -g promptfoo@0.1.0
    - pip3 install -e ".[dev,test]"
  script:
    - python -m pydanticai_api_template.cli prompt-test
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
```

### Best Practices

- **Version pinning**: Specify exact versions in CI configs
- **Cost management**: Consider scheduled rather than per-commit runs for LLM tests
- **Selective testing**: For large prompt sets, test only changed prompts on PRs
- **Artifacts**: Save test results as artifacts for documentation

## Testing Prompts with Promptfoo

The template includes support for testing prompts using the [Promptfoo](https://github.com/promptfoo/promptfoo) tool. This allows you to define test cases for your prompts and ensure they produce the expected outputs with different inputs.

### Running Prompt Tests

To run promptfoo tests using the CLI:

```bash
# Run all prompt tests
pat prompt-test

# Run tests with a specific config file
pat prompt-test --config custom-config.yaml

# Open the web UI after running tests
pat prompt-test --view

# Show detailed test information
pat prompt-test --verbose
```

### Prompt Test Configuration

Prompt tests are defined in the `promptfoo/config.yaml` file. Here's how to structure it:

```yaml
# Define your prompts
prompts:
  - id: chat
    label: Chat Prompt
    raw: |
      You are a helpful assistant. Please respond to the following message:

      {{input}}

  - id: story
    label: Story Prompt
    raw: |
      Generate a story idea with a title and premise based on:

      {{input}}

# Define your AI providers
providers:
  - id: openai:gpt-4o
    config:
      headers:
        Authorization: "Bearer ${OPENAI_API_KEY}"

# Define test cases
testCases:
  - description: Basic greeting
    vars:
      input: "Hello, how are you today?"
    assert:
      - type: llm-rubric
        value: "The response should be a polite greeting."
      - type: javascript
        value: "output.length > 10"

  - description: Story about space
    vars:
      input: "Write a story about space exploration"
    assert:
      - type: llm-rubric
        value: "The response should include a creative story idea with a title and premise related to space exploration."
      - type: javascript
        value: "output.includes('space') || output.includes('exploration')"
```

### Writing Effective Prompt Tests

1. **Define clear assertions**: Use a combination of `llm-rubric` for qualitative evaluation and `javascript` for objective criteria.

2. **Test with diverse inputs**: Include edge cases and different types of requests.

3. **Check for specific content**: Verify that responses contain required information.

4. **Keep tests focused**: Each test should check a specific aspect of the prompt's behavior.

### Testing Checklist for Prompts

- [ ] Tests for different prompt variations
- [ ] Tests for edge cases (very short or unusual inputs)
- [ ] Tests for content that should be included in responses
- [ ] Tests for response length and format
- [ ] Tests for adherence to specified instructions

### Troubleshooting Prompt Tests

1. **Missing Node.js or npm**:
   - The prompt-test command requires Node.js and npm to be installed
   - In the development container, these are pre-installed

2. **API key issues**:
   - Make sure your .env file contains the required API keys
   - The prompt-test command automatically loads environment variables from .env

3. **Configuration file not found**:
   - Verify the path to your promptfoo configuration file
   - The default location is `promptfoo/config.yaml` in the project root
