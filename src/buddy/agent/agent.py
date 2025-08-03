"""Simple agent implementation with tool calling."""

import json
import os
from typing import Any

from dotenv import load_dotenv

from buddy.llm.llm import call_llm
from buddy.tools.tool import Tool

load_dotenv()

os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")


class Agent:
    """Simple agent that can interact with LLM and call tools."""

    def __init__(self, tools: list[Tool] | None = None, model: str = "gemini/gemini-2.0-flash-exp"):
        """Initialize agent with tools and model."""
        self.tools = tools or []
        self.model = model
        self.messages: list[dict[str, Any]] = []

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent."""
        self.tools.append(tool)

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get OpenAI-compatible tool schemas."""
        return [tool.get_input_schema() for tool in self.tools]

    def _find_tool(self, name: str) -> Tool | None:
        """Find a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    async def run(self, prompt: str, max_iterations: int = 10) -> str:
        """Run the agent with a prompt, handling tool calls."""
        self.messages = [{"role": "user", "content": prompt}]

        for _ in range(max_iterations):
            # Get tool schemas if we have tools
            tools = self._get_tool_schemas() if self.tools else None

            # Call LLM
            response = call_llm(messages=self.messages, model=self.model, tools=tools)

            # Extract response content and tool calls
            message = response.choices[0].message
            content = message.content or ""
            tool_calls = getattr(message, "tool_calls", None)

            # Add assistant message
            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ]
            self.messages.append(assistant_msg)

            # If no tool calls, we're done
            if not tool_calls:
                return content

            # Execute tool calls
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    tool = self._find_tool(tool_name)

                    if tool:
                        result = tool.run(**arguments)
                        result_str = str(result)
                    else:
                        result_str = f"Error: Tool '{tool_name}' not found"

                except Exception as e:
                    result_str = f"Error executing {tool_name}: {e!s}"

                # Add tool result message
                self.messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result_str})

        return "Maximum iterations reached"
