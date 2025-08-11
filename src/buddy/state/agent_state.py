"""Agent execution state model.

This module defines a Pydantic model that captures the mutable state an agent
may need during execution, including available tools, authentication tokens,
model configuration, and conversation history.
"""

from typing import Any

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Container for agent runtime state.

    Designed to be passed through agent loops, tool calls, or persisted between
    steps. Keeps only JSON-serializable structures for portability.
    """

    # Identity and description
    name: str = Field(default="agent", description="Human-readable agent name")
    description: str | None = Field(default=None, description="Short agent description/system purpose")

    # Session/trace identifiers
    session_id: str | None = Field(default=None, description="Logical session identifier")
    trace_id: str | None = Field(default=None, description="Correlation/trace identifier for observability")

    # LLM configuration
    model: str = Field(default="github/gpt-4.1-mini", description="Model identifier used for completions")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    tool_choice: str | dict[str, Any] | None = Field(
        default=None, description="Tool selection strategy passed to the LLM"
    )
    response_format: dict[str, Any] | None = Field(default=None, description="Response format hints passed to the LLM")

    # Tools and specifications
    tool_names: list[str] = Field(default_factory=list, description="Names of tools available to the agent")
    tool_ids: list[str] = Field(default_factory=list, description="Tool call IDs observed during this run")
    tool_specs: list[dict[str, Any]] = Field(
        default_factory=list, description="OpenAI/LiteLLM compatible tool specifications"
    )

    # Authentication and environment
    auth_tokens: dict[str, str] = Field(default_factory=dict, description="Service name to auth token mapping")
    environment: dict[str, str] = Field(
        default_factory=dict, description="Environment variables relevant for execution"
    )

    # Execution configuration and scratch space
    run_config: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary per-run configuration passed to tools/LLM"
    )
    scratchpad: dict[str, Any] = Field(
        default_factory=dict, description="Ephemeral working data for intermediate results"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="User-defined metadata or tags")

    model_config = {
        "arbitrary_types_allowed": False,
        "frozen": False,
        "extra": "allow",
    }
