"""
Configuration system for A2A agents.

This module provides configuration management that integrates with the
existing Buddy model system and supports flexible LLM provider selection.
"""

import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

from .llm_client import MODEL_PRESETS, LiteLLMClient, create_llm_client

load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for LLM client settings."""

    model: str = "gemini/gemini-2.0-flash-exp"
    temperature: float = 0.7
    max_tokens: int | None = None
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for A2A agent settings."""

    name: str = "BuddyA2AAgent"
    description: str = "Buddy AI Assistant with A2A protocol support"
    version: str = "1.0.0"
    system_prompt: str | None = None
    llm_config: LLMConfig = field(default_factory=LLMConfig)


@dataclass
class A2AConfig:
    """Configuration for A2A protocol settings."""

    host: str = "localhost"
    port: int = 8000
    use_mock: bool = True  # Default to mock for development


@dataclass
class BuddyA2AConfig:
    """Complete configuration for Buddy A2A system."""

    agent: AgentConfig = field(default_factory=AgentConfig)
    a2a: A2AConfig = field(default_factory=A2AConfig)
    tools: list[str] = field(default_factory=list)  # Tool names to load


class ConfigManager:
    """
    Configuration manager for Buddy A2A system.

    This class provides configuration management with environment variable
    support and integration with existing Buddy systems.
    """

    @staticmethod
    def load_from_env() -> BuddyA2AConfig:
        """Load configuration from environment variables."""
        config = BuddyA2AConfig()

        # LLM Configuration
        config.agent.llm_config.model = os.getenv("BUDDY_A2A_MODEL", ConfigManager._detect_default_model())
        config.agent.llm_config.temperature = float(os.getenv("BUDDY_A2A_TEMPERATURE", "0.7"))

        max_tokens = os.getenv("BUDDY_A2A_MAX_TOKENS")
        if max_tokens:
            config.agent.llm_config.max_tokens = int(max_tokens)

        # Agent Configuration
        config.agent.name = os.getenv("BUDDY_A2A_AGENT_NAME", config.agent.name)
        config.agent.description = os.getenv("BUDDY_A2A_AGENT_DESCRIPTION", config.agent.description)
        config.agent.version = os.getenv("BUDDY_A2A_VERSION", config.agent.version)

        # A2A Protocol Configuration
        config.a2a.host = os.getenv("BUDDY_A2A_HOST", config.a2a.host)
        config.a2a.port = int(os.getenv("BUDDY_A2A_PORT", str(config.a2a.port)))
        config.a2a.use_mock = os.getenv("BUDDY_A2A_USE_MOCK", "true").lower() == "true"

        return config

    @staticmethod
    def _detect_default_model() -> str:
        """Detect the best default model based on available API keys."""
        # Check for API keys and return appropriate model
        if os.getenv("GOOGLE_API_KEY"):
            return "gemini/gemini-2.0-flash-exp"
        elif os.getenv("OPENAI_API_KEY"):
            return "gpt-4o-mini"
        elif os.getenv("ANTHROPIC_API_KEY"):
            return "claude-3-haiku-20240307"
        elif os.getenv("GITHUB_TOKEN"):
            return "github/gpt-4o-mini"
        else:
            # Fallback to Gemini (free tier available)
            return "gemini/gemini-2.0-flash-exp"

    @staticmethod
    def create_llm_client(config: LLMConfig) -> LiteLLMClient:
        """Create an LLM client from configuration."""
        return create_llm_client(
            model=config.model, temperature=config.temperature, max_tokens=config.max_tokens, **config.extra_params
        )

    @staticmethod
    def get_available_models() -> dict[str, dict[str, Any]]:
        """Get information about available models."""
        models = {}

        # Add preset models
        for preset_name, preset_config in MODEL_PRESETS.items():
            models[preset_name] = {
                "model": preset_config["model"],
                "temperature": preset_config["temperature"],
                "source": "preset",
                "available": ConfigManager._check_model_availability(preset_config["model"]),
            }

        # Add detected models based on API keys
        detected = ConfigManager._get_detected_models()
        for model_name, model_info in detected.items():
            if model_name not in models:
                models[model_name] = model_info

        return models

    @staticmethod
    def _check_model_availability(model: str) -> bool:
        """Check if a model is available based on API keys."""
        if model.startswith("gemini/"):
            return bool(os.getenv("GOOGLE_API_KEY"))
        elif model.startswith("gpt-") or model.startswith("openai/"):
            return bool(os.getenv("OPENAI_API_KEY"))
        elif model.startswith("claude-"):
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        elif model.startswith("github/"):
            return bool(os.getenv("GITHUB_TOKEN"))
        else:
            return False

    @staticmethod
    def _get_detected_models() -> dict[str, dict[str, Any]]:
        """Get models based on detected API keys."""
        detected = {}

        if os.getenv("GOOGLE_API_KEY"):
            detected["google_default"] = {
                "model": "gemini/gemini-2.0-flash-exp",
                "temperature": 0.7,
                "source": "detected",
                "available": True,
                "provider": "Google",
            }

        if os.getenv("OPENAI_API_KEY"):
            detected["openai_default"] = {
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "source": "detected",
                "available": True,
                "provider": "OpenAI",
            }

        if os.getenv("ANTHROPIC_API_KEY"):
            detected["anthropic_default"] = {
                "model": "claude-3-haiku-20240307",
                "temperature": 0.7,
                "source": "detected",
                "available": True,
                "provider": "Anthropic",
            }

        if os.getenv("GITHUB_TOKEN"):
            detected["github_default"] = {
                "model": "github/gpt-4o-mini",
                "temperature": 0.7,
                "source": "detected",
                "available": True,
                "provider": "GitHub",
            }

        return detected

    @staticmethod
    def create_development_config() -> BuddyA2AConfig:
        """Create a configuration optimized for development."""
        config = BuddyA2AConfig()

        # Use mock A2A for development
        config.a2a.use_mock = True
        config.a2a.port = 8001  # Different port to avoid conflicts

        # Use a fast, cheap model for development
        if os.getenv("GOOGLE_API_KEY"):
            config.agent.llm_config.model = "gemini/gemini-2.0-flash-exp"
        else:
            config.agent.llm_config.model = "github/gpt-4o-mini"

        config.agent.llm_config.temperature = 0.5  # More deterministic for testing
        config.agent.name = "BuddyDevAgent"
        config.agent.description = "Development version of Buddy A2A Agent"

        return config

    @staticmethod
    def create_production_config() -> BuddyA2AConfig:
        """Create a configuration optimized for production."""
        config = BuddyA2AConfig()

        # Use real A2A for production
        config.a2a.use_mock = False
        config.a2a.host = os.getenv("BUDDY_A2A_PRODUCTION_HOST", "0.0.0.0")
        config.a2a.port = int(os.getenv("BUDDY_A2A_PRODUCTION_PORT", "8000"))

        # Use a capable model for production
        if os.getenv("GOOGLE_API_KEY"):
            config.agent.llm_config.model = "gemini/gemini-1.5-pro"
        elif os.getenv("OPENAI_API_KEY"):
            config.agent.llm_config.model = "gpt-4o"
        else:
            config.agent.llm_config.model = "claude-3-5-sonnet-20241022"

        config.agent.llm_config.temperature = 0.7
        config.agent.name = "BuddyA2AAgent"
        config.agent.description = "Buddy AI Assistant with comprehensive A2A protocol support"

        return config

    @staticmethod
    def validate_config(config: BuddyA2AConfig) -> list[str]:
        """
        Validate configuration and return list of issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check model availability
        if not ConfigManager._check_model_availability(config.agent.llm_config.model):
            issues.append(f"Model '{config.agent.llm_config.model}' is not available (missing API key)")

        # Check temperature range
        temp = config.agent.llm_config.temperature
        if not 0.0 <= temp <= 2.0:
            issues.append(f"Temperature {temp} is outside valid range [0.0, 2.0]")

        # Check port range
        port = config.a2a.port
        if not 1024 <= port <= 65535:
            issues.append(f"Port {port} is outside valid range [1024, 65535]")

        # Check max_tokens if specified
        max_tokens = config.agent.llm_config.max_tokens
        if max_tokens is not None and max_tokens <= 0:
            issues.append(f"max_tokens {max_tokens} must be positive")

        return issues


# Default configurations
DEFAULT_CONFIG = ConfigManager.load_from_env()
DEV_CONFIG = ConfigManager.create_development_config()
PROD_CONFIG = ConfigManager.create_production_config()
