"""
Interfaces for A2A-compatible agents.

This module defines the core abstractions needed to make agents compatible
with the Agent-to-Agent (A2A) protocol while keeping the agent logic
independent of the protocol implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class SkillType(Enum):
    """Types of skills an agent can have."""

    QUERY = "query"
    ACTION = "action"
    WORKFLOW = "workflow"


@dataclass
class Skill:
    """Represents a skill that an agent can perform."""

    name: str
    description: str
    skill_type: SkillType
    parameters: dict[str, Any]
    examples: list[str] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class Capability:
    """Represents a capability that describes what an agent can do."""

    name: str
    description: str
    version: str
    skills: list[Skill]


@dataclass
class AgentRequest:
    """Represents a request sent to an agent."""

    skill_name: str
    parameters: dict[str, Any]
    context: dict[str, Any] | None = None


@dataclass
class AgentResponse:
    """Represents a response from an agent."""

    success: bool
    result: Any
    error: str | None = None
    metadata: dict[str, Any] | None = None


class Agent(ABC):
    """
    Abstract base class for A2A-compatible agents.

    This defines the core interface that any agent must implement to be
    compatible with A2A protocol, without tying it to specific protocol details.
    """

    @abstractmethod
    def get_capabilities(self) -> list[Capability]:
        """Return the capabilities this agent provides."""
        pass

    @abstractmethod
    async def execute_skill(self, request: AgentRequest) -> AgentResponse:
        """Execute a specific skill with the given request."""
        pass

    @abstractmethod
    def get_agent_info(self) -> dict[str, Any]:
        """Return basic information about this agent."""
        pass


class A2AProtocolAdapter(Protocol):
    """
    Protocol interface for A2A server implementations.

    This defines what methods an A2A protocol adapter needs to implement
    to expose an Agent through the A2A protocol.
    """

    def start_server(self, agent: Agent, host: str = "localhost", port: int = 8000) -> None:
        """Start the A2A protocol server for the given agent."""
        ...

    def stop_server(self) -> None:
        """Stop the A2A protocol server."""
        ...

    def is_running(self) -> bool:
        """Check if the server is currently running."""
        ...


class Tool(ABC):
    """Abstract base class for agent tools."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this tool."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return a description of what this tool does."""
        pass

    @abstractmethod
    def get_parameters_schema(self) -> dict[str, Any]:
        """Return the JSON schema for this tool's parameters."""
        pass

    @abstractmethod
    async def execute(self, parameters: dict[str, Any]) -> Any:
        """Execute the tool with the given parameters."""
        pass
