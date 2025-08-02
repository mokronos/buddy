"""
A2A Agent module for creating A2A protocol compatible agents.

This module provides all the necessary components to create agents that
can work with the Agent-to-Agent (A2A) protocol while keeping the agent
logic separate from protocol implementation details.
"""

from .a2a_adapter import A2AServerAdapter, MockA2AServerAdapter, create_a2a_adapter
from .agent import LLMAgent
from .config import (
    DEFAULT_CONFIG,
    DEV_CONFIG,
    PROD_CONFIG,
    A2AConfig,
    AgentConfig,
    BuddyA2AConfig,
    ConfigManager,
    LLMConfig,
)
from .example_tools import (
    CalculatorTool,
    DataStorageTool,
    TextProcessingTool,
    TimeTool,
    get_example_tools,
)
from .integrated_agent import IntegratedA2AAgent, create_integrated_agent
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
from .llm_client import (
    MODEL_PRESETS,
    LiteLLMClient,
    create_llm_client,
    create_llm_from_preset,
)
from .tool_bridge import A2AToolBridge, ToolAdapter, create_integrated_tool_system

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_CONFIG",
    "DEV_CONFIG",
    "MODEL_PRESETS",
    "PROD_CONFIG",
    "A2AConfig",
    "A2AProtocolAdapter",
    "A2AServerAdapter",
    "A2AToolBridge",
    "Agent",
    "AgentConfig",
    "AgentRequest",
    "AgentResponse",
    "BuddyA2AConfig",
    "CalculatorTool",
    "Capability",
    "ConfigManager",
    "DataStorageTool",
    "IntegratedA2AAgent",
    "LLMAgent",
    "LLMConfig",
    "LiteLLMClient",
    "MockA2AServerAdapter",
    "Skill",
    "SkillType",
    "TextProcessingTool",
    "TimeTool",
    "Tool",
    "ToolAdapter",
    "create_a2a_adapter",
    "create_integrated_agent",
    "create_integrated_tool_system",
    "create_llm_client",
    "create_llm_from_preset",
    "get_example_tools",
]
