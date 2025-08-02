"""
A2A Agent module for creating A2A protocol compatible agents.

This module provides all the necessary components to create agents that
can work with the Agent-to-Agent (A2A) protocol while keeping the agent
logic separate from protocol implementation details.
"""

from .a2a_adapter import A2AServerAdapter, MockA2AServerAdapter, create_a2a_adapter
from .agent import LLMAgent
from .example_tools import (
    CalculatorTool,
    DataStorageTool,
    TextProcessingTool,
    TimeTool,
    get_example_tools,
)
from .interfaces import (
    A2AProtocolAdapter,
    Agent,
    AgentRequest,
    AgentResponse,
    Capability,
    Skill,
    SkillType,
    Tool,
)

__version__ = "1.0.0"

__all__ = [
    # Core interfaces
    "Agent",
    "AgentRequest",
    "AgentResponse",
    "Capability",
    "Skill",
    "SkillType",
    "Tool",
    "A2AProtocolAdapter",
    # Agent implementation
    "LLMAgent",
    # A2A adapters
    "A2AServerAdapter",
    "MockA2AServerAdapter",
    "create_a2a_adapter",
    # Example tools
    "CalculatorTool",
    "TextProcessingTool",
    "TimeTool",
    "DataStorageTool",
    "get_example_tools",
]
