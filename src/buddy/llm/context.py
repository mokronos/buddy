"""
Context management for agent LLM interactions.

This module provides sophisticated context management including
token limits, message prioritization, and context compression.
"""

import json
from typing import Any


class ContextManager:
    """
    Manages context for LLM interactions with token-aware compression.

    Features:
    - Token limit enforcement
    - Message prioritization
    - Context compression
    - Tool result management
    - Dynamic context sizing
    """

    def __init__(self, max_tokens: int = 8000, reserved_tokens: int = 1000, compression_ratio: float = 0.5):
        """Initialize the context manager."""
        self.max_tokens = max_tokens
        self.reserved_tokens = reserved_tokens  # Reserve tokens for response
        self.compression_ratio = compression_ratio
        self.messages: list[dict[str, Any]] = []
        self.tool_schemas: list[dict[str, Any]] = []
        self.system_prompt: str | None = None

    def set_system_prompt(self, prompt: str):
        """Set the system prompt."""
        self.system_prompt = prompt

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None):
        """Add a message to the context."""
        message = {
            "role": role,
            "content": content,
            "timestamp": self._get_timestamp(),
            "tokens": self._estimate_tokens(content),
            "metadata": metadata or {},
        }
        self.messages.append(message)

    def add_tool_result(self, tool_name: str, arguments: dict[str, Any], result: Any):
        """Add a tool execution result to context."""
        content = (
            f"Tool: {tool_name}\nArguments: {json.dumps(arguments, indent=2)}\nResult: {json.dumps(result, indent=2)}"
        )
        self.add_message("tool", content, {"tool_name": tool_name, "type": "tool_result"})

    def set_tool_schemas(self, schemas: list[dict[str, Any]]):
        """Set available tool schemas."""
        self.tool_schemas = schemas

    def get_context_for_llm(self) -> dict[str, Any]:
        """Get properly sized context for LLM call."""
        # Manage context size first
        self.manage_context_size()

        # Build messages list
        messages = []

        # Add system prompt if available
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        # Add conversation messages
        for msg in self.messages:
            messages.append({"role": msg["role"], "content": msg["content"]})

        return {"messages": messages, "tools": self.tool_schemas, "max_tokens": self.max_tokens - self.reserved_tokens}

    def manage_context_size(self):
        """Manage context size to stay within token limits."""
        current_tokens = self._calculate_total_tokens()
        available_tokens = self.max_tokens - self.reserved_tokens

        if current_tokens <= available_tokens:
            return  # No compression needed

        # Compression strategy: keep recent messages, compress older ones
        self._compress_context(available_tokens)

    def _compress_context(self, target_tokens: int):
        """Compress context to fit within target token count."""
        if not self.messages:
            return

        # Always keep the last few messages
        keep_recent = 5
        recent_messages = self.messages[-keep_recent:] if len(self.messages) > keep_recent else self.messages
        older_messages = self.messages[:-keep_recent] if len(self.messages) > keep_recent else []

        # Calculate tokens for recent messages
        recent_tokens = sum(msg["tokens"] for msg in recent_messages)
        system_tokens = self._estimate_tokens(self.system_prompt or "")
        tool_tokens = self._estimate_tokens(json.dumps(self.tool_schemas))

        available_for_history = target_tokens - recent_tokens - system_tokens - tool_tokens

        if available_for_history <= 0:
            # Not enough space, keep only recent messages
            self.messages = recent_messages
            return

        # Compress older messages
        compressed_history = self._create_compressed_summary(older_messages, available_for_history)

        if compressed_history:
            # Replace older messages with compressed summary
            summary_message = {
                "role": "system",
                "content": f"Previous conversation summary: {compressed_history}",
                "timestamp": self._get_timestamp(),
                "tokens": self._estimate_tokens(compressed_history),
                "metadata": {"type": "compressed_summary"},
            }
            self.messages = [summary_message, *recent_messages]
        else:
            # Just keep recent messages
            self.messages = recent_messages

    def _create_compressed_summary(self, messages: list[dict[str, Any]], max_tokens: int) -> str:
        """Create a compressed summary of older messages."""
        if not messages:
            return ""

        # Simple compression: extract key information
        summary_parts = []

        for msg in messages:
            if msg["role"] == "user":
                # Summarize user requests
                content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                summary_parts.append(f"User asked: {content}")
            elif msg["role"] == "assistant":
                # Summarize assistant responses
                content = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
                summary_parts.append(f"Assistant: {content}")
            elif msg["role"] == "tool":
                # Summarize tool usage
                tool_name = msg.get("metadata", {}).get("tool_name", "unknown")
                summary_parts.append(f"Used tool: {tool_name}")

        summary = " | ".join(summary_parts)

        # Trim if still too long
        estimated_tokens = self._estimate_tokens(summary)
        if estimated_tokens > max_tokens:
            # Truncate to fit
            chars_per_token = len(summary) / estimated_tokens if estimated_tokens > 0 else 4
            max_chars = int(max_tokens * chars_per_token * 0.9)  # Be conservative
            summary = summary[:max_chars] + "..."

        return summary

    def _calculate_total_tokens(self) -> int:
        """Calculate total tokens in current context."""
        total = 0

        # System prompt
        if self.system_prompt:
            total += self._estimate_tokens(self.system_prompt)

        # Messages
        for msg in self.messages:
            total += msg["tokens"]

        # Tool schemas
        if self.tool_schemas:
            total += self._estimate_tokens(json.dumps(self.tool_schemas))

        return total

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        if not text:
            return 0
        # Rough approximation: ~4 characters per token
        return len(text) // 4 + 10  # Add small buffer

    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time

        return time.time()

    def get_context_size(self) -> dict[str, int]:
        """Get current context size information."""
        return {
            "total_tokens": self._calculate_total_tokens(),
            "max_tokens": self.max_tokens,
            "available_tokens": self.max_tokens - self._calculate_total_tokens(),
            "message_count": len(self.messages),
            "tool_schemas_count": len(self.tool_schemas),
        }

    def clear_context(self):
        """Clear all context except system prompt and tools."""
        self.messages = []

    def get_recent_messages(self, count: int = 10) -> list[dict[str, Any]]:
        """Get the most recent messages."""
        return self.messages[-count:] if len(self.messages) > count else self.messages
