"""
LiteLLM client adapter for A2A agents.

This module provides integration between the A2A agent system and
the existing LiteLLM implementation for unified LLM provider access.
"""

import json
import os
from typing import Any

from litellm import completion
from litellm.types.utils import ModelResponse


class LiteLLMClient:
    """
    LLM client adapter using LiteLLM for A2A agents.

    This client provides a bridge between the A2A agent interface and
    the existing LiteLLM implementation, supporting multiple LLM providers.
    """

    def __init__(
        self,
        model: str = "gemini/gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

    async def generate_response(
        self, prompt: str, messages: list[dict[str, str]] | None = None, tools: list[dict] | None = None, **kwargs
    ) -> str:
        """
        Generate a response using LiteLLM.

        Args:
            prompt: The main prompt text
            messages: Optional conversation history
            tools: Optional tool definitions for function calling
            **kwargs: Additional parameters for the LLM call

        Returns:
            Generated response text
        """
        call_params = self._prepare_call_params(prompt, messages, tools, **kwargs)

        try:
            response = completion(**call_params)
            return self._extract_response_content(response)
        except Exception as e:
            msg = f"LLM generation failed: {e!s}"
            raise RuntimeError(msg) from e

    def _prepare_call_params(
        self, prompt: str, messages: list[dict[str, str]] | None, tools: list[dict] | None, **kwargs
    ) -> dict:
        """Prepare parameters for LLM call."""
        if messages is None:
            messages = []

        # Add the current prompt as a user message if not already in messages
        if not messages or messages[-1].get("content") != prompt:
            messages.append({"role": "user", "content": prompt})

        # Merge parameters
        call_params = {
            "messages": messages,
            "model": self.model,
            "temperature": self.temperature,
            "stream": False,
            **self.extra_params,
            **kwargs,
        }

        # Add API key if available for Gemini
        if self.model.startswith("gemini/") and os.getenv("GOOGLE_API_KEY"):
            call_params["api_key"] = os.getenv("GOOGLE_API_KEY")

        # Add max_tokens if specified
        if self.max_tokens:
            call_params["max_tokens"] = self.max_tokens

        # Add tools if provided
        if tools:
            call_params["tools"] = tools

        return call_params

    def _extract_response_content(self, response) -> str:
        """Extract content from LLM response."""
        if isinstance(response, ModelResponse):
            # Extract content from the response
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                if choice.message and choice.message.content:
                    return choice.message.content
                elif choice.message and choice.message.tool_calls:
                    # Handle tool calls
                    return self._format_tool_calls(choice.message.tool_calls)

            return "No response generated"
        else:
            return str(response)

    def _format_tool_calls(self, tool_calls: list[Any]) -> str:
        """Format tool calls into a readable string response."""
        if not tool_calls:
            return "No tool calls generated"

        formatted_calls = []
        for tool_call in tool_calls:
            if hasattr(tool_call, "function"):
                func = tool_call.function
                formatted_calls.append({
                    "tool_name": func.name,
                    "parameters": json.loads(func.arguments) if func.arguments else {},
                    "reasoning": f"LLM wants to call {func.name}",
                })

        return json.dumps(formatted_calls, indent=2)

    async def generate_with_tools(
        self, prompt: str, tools: list[dict], messages: list[dict[str, str]] | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Generate a response with tool support.

        Args:
            prompt: The main prompt text
            tools: Tool definitions for function calling
            messages: Optional conversation history
            **kwargs: Additional parameters

        Returns:
            Dict containing response and any tool calls
        """
        # Prepare messages
        if messages is None:
            messages = []

        if not messages or messages[-1].get("content") != prompt:
            messages.append({"role": "user", "content": prompt})

        # Call with tools
        call_params = {
            "messages": messages,
            "model": self.model,
            "temperature": self.temperature,
            "tools": tools,
            "tool_choice": "auto",
            "stream": False,
            **self.extra_params,
            **kwargs,
        }

        # Add API key if available for Gemini
        if self.model.startswith("gemini/") and os.getenv("GOOGLE_API_KEY"):
            call_params["api_key"] = os.getenv("GOOGLE_API_KEY")

        if self.max_tokens:
            call_params["max_tokens"] = self.max_tokens

        try:
            response = completion(**call_params)

            if isinstance(response, ModelResponse) and response.choices:
                choice = response.choices[0]
                message = choice.message

                result = {"content": message.content or "", "tool_calls": [], "finish_reason": choice.finish_reason}

                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        if hasattr(tool_call, "function"):
                            func = tool_call.function
                            result["tool_calls"].append({
                                "id": getattr(tool_call, "id", None),
                                "name": func.name,
                                "arguments": json.loads(func.arguments) if func.arguments else {},
                            })

                return result

            return {"content": str(response), "tool_calls": [], "finish_reason": "stop"}

        except Exception as e:
            msg = f"LLM generation with tools failed: {e!s}"
            raise RuntimeError(msg) from e

    def update_model(self, model: str) -> None:
        """Update the model being used."""
        self.model = model

    def update_temperature(self, temperature: float) -> None:
        """Update the temperature setting."""
        self.temperature = temperature

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model configuration."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "extra_params": self.extra_params,
        }


def create_llm_client(model: str | None = None, temperature: float = 0.7, **kwargs) -> LiteLLMClient:
    """
    Factory function to create a LiteLLM client with sensible defaults.

    Args:
        model: Model name (defaults to Google Gemini if API key available)
        temperature: Sampling temperature
        **kwargs: Additional parameters

    Returns:
        Configured LiteLLMClient instance
    """
    # Auto-detect model based on available API keys
    if model is None:
        if os.getenv("GOOGLE_API_KEY"):
            model = "gemini/gemini-2.0-flash-exp"
        elif os.getenv("OPENAI_API_KEY"):
            model = "gpt-4o-mini"
        elif os.getenv("ANTHROPIC_API_KEY"):
            model = "claude-3-haiku-20240307"
        elif os.getenv("GITHUB_TOKEN"):
            model = "github/gpt-4o-mini"
        else:
            # Default fallback
            model = "gemini/gemini-2.0-flash-exp"

    return LiteLLMClient(model=model, temperature=temperature, **kwargs)


# Model presets for common configurations
MODEL_PRESETS = {
    "google_flash": {
        "model": "gemini/gemini-2.0-flash-exp",
        "temperature": 0.7,
    },
    "google_pro": {
        "model": "gemini/gemini-1.5-pro",
        "temperature": 0.7,
    },
    "openai_gpt4": {
        "model": "gpt-4o",
        "temperature": 0.7,
    },
    "openai_mini": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
    },
    "claude_haiku": {
        "model": "claude-3-haiku-20240307",
        "temperature": 0.7,
    },
    "claude_sonnet": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
    },
    "github_mini": {
        "model": "github/gpt-4o-mini",
        "temperature": 0.7,
    },
}


def create_llm_from_preset(preset_name: str, **overrides) -> LiteLLMClient:
    """
    Create an LLM client from a preset configuration.

    Args:
        preset_name: Name of the preset to use
        **overrides: Parameters to override in the preset

    Returns:
        Configured LiteLLMClient instance
    """
    if preset_name not in MODEL_PRESETS:
        available = ", ".join(MODEL_PRESETS.keys())
        msg = f"Unknown preset '{preset_name}'. Available: {available}"
        raise ValueError(msg)

    config = MODEL_PRESETS[preset_name].copy()
    config.update(overrides)

    return LiteLLMClient(**config)
