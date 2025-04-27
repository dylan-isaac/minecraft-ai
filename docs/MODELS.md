# Pydantic Models Guide

This document describes how to effectively use Pydantic models in the Minecraft AI, including best practices for type safety, validation, and error handling.

## Model Basics

The Minecraft AI uses Pydantic models for request/response validation, serialization, and documentation. Models are defined in `src/minecraft_ai/api/models.py`.

### Core Models

```python
from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """Request model for chat messages."""

    message: str = Field(
        ...,
        description="The user's message to the AI agent.",
        min_length=1,
        examples=["Tell me about Pydantic", "How can I use PydanticAI?"],
    )

    @classmethod
    @field_validator("message")
    def message_not_empty(cls, v: str) -> str:
        """Validate that the message is not empty."""
        if not v.strip():
            raise ValueError("Message cannot be empty or consist only of whitespace")
        return v


class ChatResponse(BaseModel):
    """Response model for the AI agent's reply."""

    reply: str = Field(
        ...,
        description="The AI agent's response.",
        examples=["Pydantic is a data validation and settings management library..."],
    )

    model_config: ClassVar[dict[str, Any]] = {
        "json_schema_extra": {
            "example": {
                "reply": "Pydantic is a Python library for data validation and settings management."
            }
        }
    }


class ErrorResponse(BaseModel):
    """Model for error responses."""

    detail: str = Field(..., description="Error message details")
    status_code: int = Field(..., description="HTTP status code")
```

## PydanticAI Structured Outputs

PydanticAI leverages Pydantic models to enforce structured outputs from LLMs, ensuring that responses are consistently formatted and validated against a defined schema.

### Defining Output Models

When working with PydanticAI, define models for the specific structures you want the LLM to generate:

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class ProductRecommendation(BaseModel):
    """Model for product recommendations from AI."""

    product_name: str = Field(..., description="Name of the recommended product")
    reasoning: str = Field(..., description="Why this product is recommended")
    price_range: str = Field(..., description="Approximate price range")
    features: List[str] = Field(..., description="Key features of the product")
    compatibility: Optional[List[str]] = Field(None, description="Compatible systems/devices")
```

### Configuring Agents with Result Types

The key to structured outputs is providing the model as a `result_type` when initializing the PydanticAI agent:

```python
from pydantic_ai import Agent

# Initialize agent with our structured output model
recommendation_agent = Agent(
    "openai:gpt-4o",
    result_type=ProductRecommendation
)

# When the agent runs, it will automatically format the response as a ProductRecommendation
result = await recommendation_agent.run("I need a new smartphone with good battery life")
recommendation = result.data  # This is a validated ProductRecommendation instance
```

### How It Works

When you specify a `result_type` in a PydanticAI agent:

1. The agent examines the Pydantic model's structure
2. It generates an appropriate system prompt extension describing the required output format
3. It attempts to parse the LLM's response as the specified model
4. If validation fails, it can retry or transform the response to match the expected structure
5. The final result is a validated Pydantic model instance

## Prompting for Structured Outputs

### Implicit Prompting via Result Type

When you specify a `result_type`, PydanticAI handles the prompting implicitly:

```python
agent = Agent("openai:gpt-4o", result_type=ChatResponse)
```

This instructs the model to generate JSON matching the structure of `ChatResponse`.

### Explicit Prompting in System Messages

For more control, you can explicitly instruct the model on output format in system prompts:

```python
from pydantic_ai import Agent, RunContext

class MovieReview(BaseModel):
    title: str
    rating: int = Field(..., ge=1, le=5)
    summary: str
    pros: List[str]
    cons: List[str]

movie_agent = Agent(
    "openai:gpt-4o",
    result_type=MovieReview,
    system_prompt=(
        "You are a movie critic who provides structured reviews. "
        "Always provide a rating between 1-5, a concise summary, "
        "and at least two pros and two cons for each movie."
    )
)
```

### Field Descriptions for Better Prompting

Include detailed descriptions in your model fields to guide the LLM:

```python
class WeatherForecast(BaseModel):
    temperature: float = Field(
        ...,
        description="Current temperature in Celsius",
        ge=-50.0,
        le=60.0
    )
    condition: str = Field(
        ...,
        description="Weather condition (e.g., 'sunny', 'cloudy', 'rainy')"
    )
    precipitation_chance: float = Field(
        ...,
        description="Probability of precipitation as a percentage",
        ge=0.0,
        le=100.0
    )
```

## System Architecture: The Flow of Data

The Minecraft AI creates a robust architecture where Pydantic models ensure type safety and validation across different components.

### End-to-End Flow

Here's how data flows through the system, with type checking at each step:

```text
User Request → FastAPI Endpoint → Pydantic Model Validation →
PydanticAI Agent (with result_type) → LLM Processing →
Structured Response → Pydantic Model Validation → JSON Response
```

### API Endpoints to Agents

API endpoints use Pydantic models for request/response validation and then pass data to PydanticAI agents:

```python
@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage) -> ChatResponse:
    # FastAPI validates the input using the ChatMessage model

    # Pass the validated message to the agent
    result = await ai_agent.run(chat_message.message)

    # Agent result is already a validated ChatResponse
    return result.data
```

### MCP Tools and Agents

MCP (Model Context Protocol) tools let external LLMs access your application functionality. Each tool should:

1. Accept validated inputs
2. Produce validated outputs
3. Handle errors consistently

```python
@server.tool()
async def get_weather(location: str, unit: str = "celsius") -> str:
    """Get weather information for a location.

    Returns formatted weather data for the specified location.
    """
    try:
        # Create a validated request object
        request = WeatherRequest(location=location, unit=unit)

        # Use a PydanticAI agent with result_type=WeatherForecast
        result = await weather_agent.run(f"Weather for {request.location}")

        # Result.data is a validated WeatherForecast
        forecast = result.data

        # Return a formatted response
        return f"Weather for {request.location}: {forecast.temperature}°{request.unit.upper()[0]}, {forecast.condition}"
    except ValidationError as e:
        return f"Invalid request: {str(e)}"
    except Exception as e:
        return f"Error processing weather request: {str(e)}"
```

### Type Safety Throughout

The entire system benefits from end-to-end type checking:

1. **Static Type Checking**: mypy verifies types across the codebase
2. **Runtime Validation**: Pydantic validates data at runtime
3. **Structured LLM Outputs**: PydanticAI ensures LLM responses match expected schemas
4. **Consistent Error Handling**: Validation errors are caught and processed uniformly

## Monitoring and Debugging

PydanticAI can be integrated with Pydantic Logfire for monitoring and debugging:

```python
import logfire
from pydantic_ai import Agent

# Configure logfire
logfire.configure()

# Enable instrumentation on the agent
agent = Agent(
    "openai:gpt-4o",
    result_type=ChatResponse,
    instrument=True  # Enable logfire instrumentation
)
```

This provides visibility into:

- Input/output validation
- LLM requests and responses
- Retry attempts
- Validation errors
- Performance metrics

## Advanced Model-Driven Techniques

### Multi-Type Response Models

For endpoints that might return different response types:

```python
from typing import Union, Literal

class TextResponse(BaseModel):
    type: Literal["text"] = "text"
    content: str

class ImageResponse(BaseModel):
    type: Literal["image"] = "image"
    url: str
    width: int
    height: int

# Union type for responses
AnyResponse = Union[TextResponse, ImageResponse]

# Agent that can return either type
multi_agent = Agent("openai:gpt-4o", result_type=AnyResponse)
```

### Dependency Injection with PydanticAI

PydanticAI supports dependency injection, letting you provide context to your agents:

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class UserContext:
    username: str
    preferences: dict

# Agent with dependencies
agent = Agent(
    "openai:gpt-4o",
    deps_type=UserContext,
    result_type=ChatResponse
)

@agent.system_prompt
def personalized_prompt(ctx: RunContext[UserContext]) -> str:
    return (
        f"The user's name is {ctx.deps.username}. "
        f"Their preferences are: {ctx.deps.preferences}. "
        "Tailor your responses accordingly."
    )

# Run with dependencies
result = await agent.run(
    "Give me some recommendations",
    deps=UserContext(
        username="alice",
        preferences={"themes": ["sci-fi", "mystery"], "format": "concise"}
    )
)
```

This creates fully type-safe, context-aware agents with structured outputs.

## Type Safety

### Field Types and Annotations

Pydantic leverages Python's type annotations to provide runtime validation:

- Use specific types (`str`, `int`, `bool`, etc.) for basic validation
- Use more complex types (`List[str]`, `Dict[str, Any]`, etc.) for nested structures
- Add `Optional` for fields that can be `None`

Example:

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class UserPreferences(BaseModel):
    name: str
    topics: List[str] = Field(..., min_items=1)
    notification_email: Optional[str] = None
```

### FastAPI Integration

FastAPI automatically uses Pydantic models for request validation and response serialization:

```python
@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage) -> ChatResponse:
    # FastAPI validates input using ChatMessage
    # And guarantees ChatResponse structure
    ...
```

### Type Checking with mypy

The project is configured with strict mypy settings to catch type errors before runtime:

```toml
[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
```

## Validation

### Field-level Validation

Use `Field()` for basic constraints:

```python
class Example(BaseModel):
    count: int = Field(..., ge=0, le=100)  # greater than or equal to 0, less than or equal to 100
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r"^\S+@\S+\.\S+$")
```

### Custom Validators

For complex validation, use field validators:

```python
from pydantic import BaseModel, field_validator

class SignupRequest(BaseModel):
    username: str
    password: str
    password_confirm: str

    @classmethod
    @field_validator("username")
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

    @classmethod
    @field_validator("password_confirm")
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v
```

### PydanticAI Integration

For AI-specific validations, use PydanticAI result types:

```python
from pydantic_ai import Agent

# Initialize agent with expected result type
agent = Agent("openai:gpt-4o", result_type=ChatResponse)

# When run, the response will be validated against ChatResponse
result = await agent.run(chat_message.message)
chat_response = result.data  # Already validated as ChatResponse
```

## Error Handling

### Validation Errors

Pydantic validation errors are automatically converted to HTTP 422 responses by FastAPI:

```python
from fastapi import HTTPException

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage) -> ChatResponse:
    # If chat_message fails validation, FastAPI returns a 422 error
    # No need to handle this manually
    ...
```

### Custom Error Responses

For custom error conditions, use the `ErrorResponse` model:

```python
from fastapi import HTTPException

if not ai_agent:
    logger.error("AI service not available")
    raise HTTPException(
        status_code=503,
        detail="AI service is not available. Please check server configuration.",
    )
```

### Error Response Structure

All errors follow a consistent JSON structure:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 500
}
```

## Best Practices

1. **Define clear models**: Create specific models for each request/response type

2. **Use descriptive field names**: Make field names intuitive and consistent

3. **Add field descriptions**: Use the `description` parameter to document each field

4. **Include examples**: Add examples to help API consumers

5. **Validate early**: Catch errors at the model validation stage rather than in business logic

6. **Use type annotations consistently**: Ensure all functions and methods have proper type hints

7. **Test model validation**: Write tests that verify your models reject invalid data

8. **Accessibility considerations**: When designing models for user interaction, ensure they support accessibility features

## Advanced Patterns

### Model Inheritance

```python
class BaseResponse(BaseModel):
    success: bool
    timestamp: datetime = Field(default_factory=datetime.now)

class SuccessResponse(BaseResponse):
    success: bool = True
    data: Any

class ErrorResponse(BaseResponse):
    success: bool = False
    error: str
    status_code: int
```

### Model Composition

```python
class Address(BaseModel):
    street: str
    city: str
    postal_code: str

class User(BaseModel):
    name: str
    address: Address
```

### Generic Models

```python
from typing import Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
```
