"""
Example tools for the A2A agent.

This module provides sample tool implementations to demonstrate
how tools can be integrated with the A2A agent system.
"""

import math
from datetime import datetime
from typing import Any

from buddy.agent.interfaces import Tool


class CalculatorTool(Tool):
    """A simple calculator tool for mathematical operations."""

    def get_name(self) -> str:
        return "calculator"

    def get_description(self) -> str:
        return "Perform mathematical calculations including basic arithmetic and common functions"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(0.5)')",
                }
            },
            "required": ["expression"],
        }

    async def execute(self, parameters: dict[str, Any]) -> Any:
        expression = parameters.get("expression", "")

        if not expression:
            msg = "Expression is required"
            raise ValueError(msg)

        try:
            # Safe evaluation of mathematical expressions
            # Only allow math functions and basic operations
            allowed_names = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
            }

            # Replace common function names
            expression = expression.replace("^", "**")  # Allow ^ for exponentiation

            result = eval(expression, {"__builtins__": {}}, allowed_names)

            return {"expression": expression, "result": result, "type": type(result).__name__}
        except Exception as e:
            msg = f"Invalid mathematical expression: {e!s}"
            raise ValueError(msg) from e


class TextProcessingTool(Tool):
    """A tool for various text processing operations."""

    def get_name(self) -> str:
        return "text_processor"

    def get_description(self) -> str:
        return "Process text with operations like word count, character count, case conversion, and text analysis"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to process"},
                "operation": {
                    "type": "string",
                    "enum": ["word_count", "char_count", "uppercase", "lowercase", "title_case", "analyze", "reverse"],
                    "description": "The operation to perform on the text",
                },
            },
            "required": ["text", "operation"],
        }

    async def execute(self, parameters: dict[str, Any]) -> Any:
        text = parameters.get("text", "")
        operation = parameters.get("operation", "")

        if not text:
            msg = "Text is required"
            raise ValueError(msg)

        if not operation:
            msg = "Operation is required"
            raise ValueError(msg)

        operations = {
            "word_count": lambda t: len(t.split()),
            "char_count": lambda t: len(t),
            "uppercase": lambda t: t.upper(),
            "lowercase": lambda t: t.lower(),
            "title_case": lambda t: t.title(),
            "reverse": lambda t: t[::-1],
            "analyze": lambda t: {
                "words": len(t.split()),
                "characters": len(t),
                "characters_no_spaces": len(t.replace(" ", "")),
                "sentences": len([s for s in t.split(".") if s.strip()]),
                "paragraphs": len([p for p in t.split("\n\n") if p.strip()]),
            },
        }

        if operation not in operations:
            msg = f"Unknown operation: {operation}"
            raise ValueError(msg)

        try:
            result = operations[operation](text)
        except Exception as e:
            msg = f"Error processing text: {e!s}"
            raise ValueError(msg) from e
        else:
            return {"original_text": text, "operation": operation, "result": result}


class TimeTool(Tool):
    """A tool for time-related operations."""

    def get_name(self) -> str:
        return "time_tool"

    def get_description(self) -> str:
        return "Get current time, format dates, and perform time calculations"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["current_time", "format_time", "time_diff"],
                    "description": "The time operation to perform",
                },
                "format": {
                    "type": "string",
                    "description": "Time format string (for format_time action)",
                    "default": "%Y-%m-%d %H:%M:%S",
                },
                "timestamp": {"type": "string", "description": "ISO timestamp (for format_time action)"},
                "time1": {"type": "string", "description": "First timestamp (for time_diff action)"},
                "time2": {"type": "string", "description": "Second timestamp (for time_diff action)"},
            },
            "required": ["action"],
        }

    async def execute(self, parameters: dict[str, Any]) -> Any:
        action = parameters.get("action", "")

        if action == "current_time":
            now = datetime.now()
            return {
                "current_time": now.isoformat(),
                "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": now.timestamp(),
            }

        elif action == "format_time":
            timestamp_str = parameters.get("timestamp")
            format_str = parameters.get("format", "%Y-%m-%d %H:%M:%S")

            if not timestamp_str:
                msg = "Timestamp is required for format_time action"
                raise ValueError(msg)

            try:
                # Parse ISO format timestamp
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                formatted = dt.strftime(format_str)
            except Exception as e:
                msg = f"Invalid timestamp format: {e!s}"
                raise ValueError(msg) from e
            else:
                return {"original_timestamp": timestamp_str, "format": format_str, "formatted_time": formatted}

        elif action == "time_diff":
            time1_str = parameters.get("time1")
            time2_str = parameters.get("time2")

            if not time1_str or not time2_str:
                msg = "Both time1 and time2 are required for time_diff action"
                raise ValueError(msg)

            try:
                dt1 = datetime.fromisoformat(time1_str.replace("Z", "+00:00"))
                dt2 = datetime.fromisoformat(time2_str.replace("Z", "+00:00"))

                diff = dt2 - dt1
            except Exception as e:
                msg = f"Invalid timestamp format: {e!s}"
                raise ValueError(msg) from e
            else:
                return {
                    "time1": time1_str,
                    "time2": time2_str,
                    "difference_seconds": diff.total_seconds(),
                    "difference_days": diff.days,
                    "difference_readable": str(diff),
                }

        else:
            msg = f"Unknown action: {action}"
            raise ValueError(msg)


class DataStorageTool(Tool):
    """A simple in-memory data storage tool for the agent."""

    def __init__(self):
        self._storage = {}

    def get_name(self) -> str:
        return "data_storage"

    def get_description(self) -> str:
        return "Store and retrieve data during agent execution"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["store", "retrieve", "list", "delete", "clear"],
                    "description": "The storage operation to perform",
                },
                "key": {"type": "string", "description": "The key to store/retrieve data under"},
                "value": {"description": "The value to store (can be any JSON-serializable data)"},
            },
            "required": ["action"],
        }

    async def execute(self, parameters: dict[str, Any]) -> Any:
        action = parameters.get("action", "")
        key = parameters.get("key")
        value = parameters.get("value")

        action_handlers = {
            "store": self._handle_store,
            "retrieve": self._handle_retrieve,
            "list": self._handle_list,
            "delete": self._handle_delete,
            "clear": self._handle_clear,
        }

        if action not in action_handlers:
            msg = f"Unknown action: {action}"
            raise ValueError(msg)

        return action_handlers[action](key, value)

    def _handle_store(self, key: str | None, value: Any) -> dict[str, Any]:
        """Handle store action."""
        if not key:
            msg = "Key is required for store action"
            raise ValueError(msg)

        self._storage[key] = value
        return {"action": "store", "key": key, "value": value, "stored_at": datetime.now().isoformat()}

    def _handle_retrieve(self, key: str | None, value: Any) -> dict[str, Any]:
        """Handle retrieve action."""
        if not key:
            msg = "Key is required for retrieve action"
            raise ValueError(msg)

        if key not in self._storage:
            msg = f"Key '{key}' not found in storage"
            raise ValueError(msg)

        return {"action": "retrieve", "key": key, "value": self._storage[key]}

    def _handle_list(self, key: str | None, value: Any) -> dict[str, Any]:
        """Handle list action."""
        return {"action": "list", "keys": list(self._storage.keys()), "count": len(self._storage)}

    def _handle_delete(self, key: str | None, value: Any) -> dict[str, Any]:
        """Handle delete action."""
        if not key:
            msg = "Key is required for delete action"
            raise ValueError(msg)

        if key not in self._storage:
            msg = f"Key '{key}' not found in storage"
            raise ValueError(msg)

        deleted_value = self._storage.pop(key)
        return {"action": "delete", "key": key, "deleted_value": deleted_value}

    def _handle_clear(self, key: str | None, value: Any) -> dict[str, Any]:
        """Handle clear action."""
        count = len(self._storage)
        self._storage.clear()
        return {"action": "clear", "cleared_count": count}


def get_example_tools() -> list[Tool]:
    """Return a list of example tools for testing the A2A agent."""
    return [
        CalculatorTool(),
        TextProcessingTool(),
        TimeTool(),
        DataStorageTool(),
    ]
