"""
Bridge between existing Tool class and A2A Tool interface.

This module provides adapters to make existing tools compatible with
the A2A agent system while preserving the original functionality.
"""

from typing import Any

from ..tools.tool import Tool as BuddyTool
from .interfaces import Tool as A2ATool


class ToolAdapter(A2ATool):
    """
    Adapter that wraps a Buddy Tool to work with A2A interface.

    This allows existing tools to be used seamlessly with the A2A agent system
    without requiring changes to the original tool implementations.
    """

    def __init__(self, buddy_tool: BuddyTool):
        self.buddy_tool = buddy_tool

    def get_name(self) -> str:
        """Return the name of this tool."""
        return self.buddy_tool.name

    def get_description(self) -> str:
        """Return a description of what this tool does."""
        return self.buddy_tool.description

    def get_parameters_schema(self) -> dict[str, Any]:
        """Return the JSON schema for this tool's parameters."""
        try:
            # Get the OpenAI function schema from the existing tool
            openai_schema = self.buddy_tool.get_input_schema()

            # Convert OpenAI function schema to JSON schema
            if "function" in openai_schema:
                function_def = openai_schema["function"]
                return function_def.get("parameters", {})
        except Exception:
            # Fallback schema if extraction fails
            return {
                "type": "object",
                "properties": {"input": {"type": "string", "description": "Input for the tool"}},
                "required": [],
            }
        else:
            # Fallback to basic schema
            return {"type": "object", "properties": {}, "required": []}

    async def execute(self, parameters: dict[str, Any]) -> Any:
        """Execute the tool with the given parameters."""
        try:
            # Call the original tool's run method
            # The original tool expects keyword arguments
            result = self.buddy_tool.run(**parameters)
        except Exception as e:
            msg = f"Tool execution failed: {e!s}"
            raise RuntimeError(msg) from e
        else:
            return result


class A2AToolBridge:
    """
    Bridge for managing tool conversion between Buddy and A2A systems.

    This class provides utilities for converting between the two tool systems
    and managing collections of adapted tools.
    """

    @staticmethod
    def adapt_buddy_tool(buddy_tool: BuddyTool) -> A2ATool:
        """Convert a Buddy Tool to an A2A Tool."""
        return ToolAdapter(buddy_tool)

    @staticmethod
    def adapt_buddy_tools(buddy_tools: list[BuddyTool]) -> list[A2ATool]:
        """Convert a list of Buddy Tools to A2A Tools."""
        return [A2AToolBridge.adapt_buddy_tool(tool) for tool in buddy_tools]

    @staticmethod
    def get_openai_function_schemas(buddy_tools: list[BuddyTool]) -> list[dict[str, Any]]:
        """
        Get OpenAI function schemas from Buddy tools.

        This is useful for LLM function calling integration.
        """
        schemas = []
        for tool in buddy_tools:
            try:
                schema = tool.get_input_schema()
                schemas.append(schema)
            except Exception:
                # Create a fallback schema
                fallback_schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {"input": {"type": "string", "description": "Input for the tool"}},
                            "required": [],
                        },
                    },
                }
                schemas.append(fallback_schema)
        return schemas

    @staticmethod
    def create_tool_map(buddy_tools: list[BuddyTool]) -> dict[str, BuddyTool]:
        """Create a mapping of tool names to tools for quick lookup."""
        return {tool.name: tool for tool in buddy_tools}

    @staticmethod
    def execute_buddy_tool(tool_name: str, parameters: dict[str, Any], tool_map: dict[str, BuddyTool]) -> Any:
        """
        Execute a Buddy tool by name with parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            tool_map: Mapping of tool names to tool instances

        Returns:
            Result from the tool execution
        """
        if tool_name not in tool_map:
            msg = f"Tool '{tool_name}' not found"
            raise ValueError(msg)

        tool = tool_map[tool_name]
        return tool.run(**parameters)

    @staticmethod
    def get_tool_info(buddy_tools: list[BuddyTool]) -> list[dict[str, Any]]:
        """
        Get information about all tools.

        Returns a list of dictionaries containing tool metadata.
        """
        tool_info = []
        for tool in buddy_tools:
            try:
                schema = tool.get_input_schema()
                parameters = {}
                if "function" in schema and "parameters" in schema["function"]:
                    parameters = schema["function"]["parameters"]

                tool_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters,
                    "schema": schema,
                })
            except Exception as e:
                # Fallback info
                tool_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {},
                    "schema": {},
                    "error": str(e),
                })

        return tool_info


def create_integrated_tool_system(buddy_tools: list[BuddyTool]) -> dict[str, Any]:
    """
    Create an integrated tool system for A2A agents.

    This function takes a list of Buddy tools and creates all the necessary
    components for integration with A2A agents:
    - A2A-compatible tool adapters
    - OpenAI function schemas for LLM integration
    - Tool mapping for quick lookup
    - Tool information for introspection

    Args:
        buddy_tools: List of Buddy Tool instances

    Returns:
        Dictionary containing all tool system components
    """
    bridge = A2AToolBridge()

    return {
        "a2a_tools": bridge.adapt_buddy_tools(buddy_tools),
        "openai_schemas": bridge.get_openai_function_schemas(buddy_tools),
        "tool_map": bridge.create_tool_map(buddy_tools),
        "tool_info": bridge.get_tool_info(buddy_tools),
        "buddy_tools": buddy_tools,
    }
