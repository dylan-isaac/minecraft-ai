# Observability and Testing

This document describes the observability and testing infrastructure of the PydanticAI API Template project.

## Observability with LogFire

The project includes integration with [LogFire](https://logfire.pydantic.dev/docs/), which provides robust observability for your AI-powered applications.

### Setup

Observability is configured through environment variables:

```dotenv
LOGFIRE_TOKEN="your-write-token"
LOGFIRE_PROJECT_ID="pydantic-ai-template"
LOGFIRE_ENABLED="true"
```

These variables should be set in your `.env` file. For development or CI environments where you don't want to send telemetry, set `LOGFIRE_ENABLED="false"`.

### Local Development Setup

For local development, we recommend using the Logfire CLI to authenticate:

```bash
# Authenticate with Logfire
logfire auth

# Set the current project to pydantic-ai-template
logfire projects use pydantic-ai-template
```

When using the development container, you can use these convenient aliases:

- `auth-logfire` - Authenticate with Logfire
- `use-logfire` - Set the current project to pydantic-ai-template

### Production Setup

For production environments, use a write token:

1. Generate a write token through the Logfire dashboard (Settings → Write Tokens)
2. Set the `LOGFIRE_TOKEN` environment variable in your production environment
3. Ensure `LOGFIRE_ENABLED` is set to `true`

### Usage

Observability is automatically set up for the main components:

1. **API Server**: All FastAPI endpoints are instrumented
2. **MCP Server**: The Model Context Protocol server is instrumented
3. **PydanticAI Agents**: All agents are instrumented with the `instrument=True` parameter

You can also add custom logging in your code:

```python
import logfire

# Log an event
logfire.info("User action completed", user_id="123", action="login")

# Create a span for measuring performance
with logfire.span("database_query") as span:
    # Set attributes on the span
    span.set_attributes({"query_type": "user_lookup", "user_id": "123"})

    # Perform your operation
    result = perform_database_query()

    # Set the status (success or error)
    if result:
        span.set_status("ok")
    else:
        span.set_status("error", "Query failed")
```

### Viewing Logs and Traces

You can view your logs and traces in the LogFire dashboard:

1. Go to [https://logfire-us.pydantic.dev](https://logfire-us.pydantic.dev)
2. Navigate to your project
3. Use the Live View to see real-time logs
4. Create dashboards for recurring metrics

### PydanticAI Integration

PydanticAI integration is automatically set up when available. This provides visibility into:

1. LLM calls and responses
2. Prompt construction and token usage
3. Model latency and performance metrics
4. Validation errors and model failures

## Testing Infrastructure

### Unit Testing

The project uses pytest for unit testing with good practices:

1. Tests are organized in the `tests/` directory
2. The `conftest.py` file provides common fixtures
3. Code coverage tracking is enabled

To run the tests:

```bash
# Run all tests
pat test

# Run tests with coverage reporting
pytest --cov=pydanticai_api_template tests/
```

### Testing Strategies

The project follows these testing strategies:

1. **Unit Tests**: Tests for individual components in isolation
2. **Mocking**: Uses pytest fixtures and unittest.mock for mocking dependencies
3. **Integration Tests**: Tests for complete API flows
4. **Environment Isolation**: Tests run in a separate environment with mock credentials

### Prompt Testing with PromptFoo

The project includes [PromptFoo](https://promptfoo.dev/) for testing AI prompts:

1. Prompt templates are stored in `promptfoo/prompts/`
2. Test cases are defined in `promptfoo/config.yaml`
3. Results can be viewed through the PromptFoo web UI

To run prompt tests:

```bash
# Run tests
pat prompt-test

# Run tests and open the web UI
pat prompt-test --view
```

### CI/CD with GitHub Actions

The project includes GitHub Actions workflows for continuous integration:

1. Running linters (ruff)
2. Type checking (mypy)
3. Unit tests with code coverage reporting
4. Dependency vulnerability scanning

The workflow file is located at `.github/workflows/test.yml`.

## Best Practices

When adding new functionality, follow these best practices for observability and testing:

1. **Add LogFire spans** for performance-critical operations
2. **Track request contexts** using LogFire's context features
3. **Write tests** for all new functionality
4. **Use test-driven development** when appropriate
5. **Test error cases** along with success cases
6. **Create prompt tests** for new AI interactions

## Adding Custom Metrics

You can add custom metrics to track important business or technical KPIs:

```python
from logfire import metrics

# Create a counter
request_counter = metrics.counter("api_requests", description="Count of API requests")

# Increment the counter
request_counter.add(1, {"endpoint": "/chat", "status": "success"})
```
