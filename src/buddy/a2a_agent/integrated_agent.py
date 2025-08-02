"""
Integrated A2A agent using LiteLLM and existing Buddy tool system.

This module provides an enhanced A2A agent that integrates seamlessly with
the existing Buddy architecture while maintaining A2A protocol compatibility.
"""

import json
from typing import Any

from ..tools.tool import Tool as BuddyTool
from .agent import LLMAgent
from .interfaces import AgentRequest, AgentResponse
from .llm_client import LiteLLMClient, create_llm_client
from .tool_bridge import A2AToolBridge, create_integrated_tool_system


class IntegratedA2AAgent(LLMAgent):
    """
    Enhanced A2A agent that integrates with existing Buddy systems.

    This agent uses LiteLLM for model access and can work with existing
    Buddy tools while maintaining full A2A protocol compatibility.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        buddy_tools: list[BuddyTool] | None = None,
        llm_client: LiteLLMClient | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        system_prompt: str | None = None,
        **llm_kwargs,
    ):
        """
        Initialize the integrated A2A agent.

        Args:
            name: Agent name
            description: Agent description
            version: Agent version
            buddy_tools: List of existing Buddy tools
            llm_client: Pre-configured LiteLLM client (optional)
            model: Model name for auto-creating LLM client
            temperature: LLM temperature setting
            system_prompt: Custom system prompt
            **llm_kwargs: Additional LLM configuration
        """
        # Set up LLM client
        if llm_client is None:
            llm_client = create_llm_client(model=model, temperature=temperature, **llm_kwargs)

        self.llm_client = llm_client

        # Store attributes needed for system prompt generation
        self.name = name
        self.description = description

        # Set up tool system
        buddy_tools = buddy_tools or []
        self.tool_system = create_integrated_tool_system(buddy_tools)

        # Initialize parent with A2A-compatible tools
        super().__init__(
            name=name,
            description=description,
            version=version,
            llm_client=llm_client,
            tools=self.tool_system["a2a_tools"],
            system_prompt=system_prompt or self._create_enhanced_system_prompt(),
        )

        # Store additional components
        self.buddy_tools = buddy_tools
        self.openai_schemas = self.tool_system["openai_schemas"]
        self.buddy_tool_map = self.tool_system["tool_map"]

    def _create_enhanced_system_prompt(self) -> str:
        """Create an enhanced system prompt with tool information."""
        tool_descriptions = []

        for tool_info in self.tool_system["tool_info"]:
            tool_name = tool_info["name"]
            tool_desc = tool_info["description"]
            tool_descriptions.append(f"- {tool_name}: {tool_desc}")

        tools_section = "\n".join(tool_descriptions) if tool_descriptions else "No tools available."

        return f"""You are {self.name}, {self.description}

Available tools:
{tools_section}

When executing skills:
1. Analyze the request carefully to understand what the user wants
2. Determine which tool(s) would be most appropriate for the task
3. Use tools with correct parameters to complete the request
4. Provide clear, helpful responses based on the results
5. If you need to use a tool, respond with properly formatted JSON containing tool name and parameters

You have access to advanced reasoning capabilities and can chain multiple tool calls if needed.
Always be helpful, accurate, and concise in your responses."""

    async def _call_llm(self, prompt: str, use_tools: bool = False) -> str:
        """Enhanced LLM call using LiteLLM with optional tool support."""
        try:
            if use_tools and self.openai_schemas:
                # Use tools with function calling
                response = await self.llm_client.generate_with_tools(prompt=prompt, tools=self.openai_schemas)

                # Handle tool calls
                if response.get("tool_calls"):
                    return self._format_tool_response(response)
                else:
                    return response.get("content", "No response generated")
            else:
                # Regular text generation
                return await self.llm_client.generate_response(prompt)

        except Exception as e:
            msg = f"LLM call failed: {e!s}"
            raise RuntimeError(msg) from e

    def _format_tool_response(self, llm_response: dict[str, Any]) -> str:
        """Format LLM response with tool calls into instruction format."""
        tool_calls = llm_response.get("tool_calls", [])

        if not tool_calls:
            return llm_response.get("content", "No tool calls generated")

        # Format as instructions for tool execution
        if len(tool_calls) == 1:
            tool_call = tool_calls[0]
            return json.dumps({
                "tool_name": tool_call["name"],
                "parameters": tool_call["arguments"],
                "reasoning": f"LLM determined {tool_call['name']} is needed for this task",
            })
        else:
            # Multiple tool calls
            formatted_calls = []
            for tool_call in tool_calls:
                formatted_calls.append({
                    "tool_name": tool_call["name"],
                    "parameters": tool_call["arguments"],
                    "reasoning": f"LLM wants to use {tool_call['name']}",
                })
            return json.dumps(formatted_calls)

    async def _handle_tool_execution(self, request: AgentRequest) -> AgentResponse:
        """Enhanced tool execution with LLM reasoning and function calling."""
        task = request.parameters.get("task", "")
        tool_params = request.parameters.get("tool_params", {})

        if not self.llm_client:
            return AgentResponse(
                success=False,
                result=None,
                error="No LLM client configured for tool execution reasoning",
            )

        # Enhanced prompt for tool selection
        prompt = f"""Task: {task}

Available tools and their capabilities:
{self._format_available_tools()}

Additional context: {json.dumps(tool_params, indent=2) if tool_params else "None"}

Determine which tool(s) to use to complete this task. Consider:
1. What the user is asking for
2. Which tools are most appropriate
3. What parameters each tool needs
4. Whether multiple tools might be needed

Respond with your reasoning and tool selection."""

        try:
            # Use LLM with function calling for better tool selection
            llm_response = await self._call_llm(prompt, use_tools=True)

            # Parse and execute tools
            tool_instructions = self._parse_tool_instructions(llm_response)

            # Execute tools using Buddy tool system for better performance
            results = []
            for instruction in tool_instructions:
                tool_result = await self._execute_buddy_tool(instruction["tool_name"], instruction["parameters"])
                results.append({
                    "tool": instruction["tool_name"],
                    "result": tool_result,
                    "reasoning": instruction.get("reasoning", ""),
                })

            return AgentResponse(
                success=True,
                result=results,
                metadata={"skill": "tool_execution", "task": task, "llm_model": self.llm_client.model},
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                result=None,
                error=f"Enhanced tool execution error: {e!s}",
            )

    async def _execute_buddy_tool(self, tool_name: str, parameters: dict[str, Any]) -> Any:
        """Execute a Buddy tool directly for better performance."""
        return A2AToolBridge.execute_buddy_tool(
            tool_name=tool_name, parameters=parameters, tool_map=self.buddy_tool_map
        )

    def _format_available_tools(self) -> str:
        """Format available tools for LLM prompt."""
        tool_descriptions = []
        for tool_info in self.tool_system["tool_info"]:
            name = tool_info["name"]
            desc = tool_info["description"]
            params = tool_info.get("parameters", {})

            param_info = ""
            if params.get("properties"):
                param_names = list(params["properties"].keys())
                param_info = f" (parameters: {', '.join(param_names)})"

            tool_descriptions.append(f"- {name}: {desc}{param_info}")

        return "\n".join(tool_descriptions)

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the LLM model configuration."""
        base_info = super().get_agent_info()
        llm_info = self.llm_client.get_model_info()

        return {
            **base_info,
            "llm_model": llm_info,
            "buddy_tools_count": len(self.buddy_tools),
            "openai_schemas_count": len(self.openai_schemas),
        }

    def update_model(self, model: str) -> None:
        """Update the LLM model being used."""
        self.llm_client.update_model(model)

    def update_temperature(self, temperature: float) -> None:
        """Update the LLM temperature setting."""
        self.llm_client.update_temperature(temperature)

    def add_buddy_tool(self, tool: BuddyTool) -> None:
        """Add a new Buddy tool to the agent."""
        self.buddy_tools.append(tool)

        # Recreate tool system
        self.tool_system = create_integrated_tool_system(self.buddy_tools)

        # Update components
        self.tools = self.tool_system["a2a_tools"]
        self.openai_schemas = self.tool_system["openai_schemas"]
        self.buddy_tool_map = self.tool_system["tool_map"]
        self.tool_map = {tool.get_name(): tool for tool in self.tools}

    def remove_buddy_tool(self, tool_name: str) -> bool:
        """Remove a Buddy tool by name."""
        original_count = len(self.buddy_tools)
        self.buddy_tools = [t for t in self.buddy_tools if t.name != tool_name]

        if len(self.buddy_tools) < original_count:
            # Recreate tool system
            self.tool_system = create_integrated_tool_system(self.buddy_tools)

            # Update components
            self.tools = self.tool_system["a2a_tools"]
            self.openai_schemas = self.tool_system["openai_schemas"]
            self.buddy_tool_map = self.tool_system["tool_map"]
            self.tool_map = {tool.get_name(): tool for tool in self.tools}
            return True

        return False


def create_integrated_agent(
    name: str, description: str, buddy_tools: list[BuddyTool] | None = None, model: str | None = None, **kwargs
) -> IntegratedA2AAgent:
    """
    Factory function to create an integrated A2A agent.

    Args:
        name: Agent name
        description: Agent description
        buddy_tools: List of Buddy tools to include
        model: LLM model to use
        **kwargs: Additional configuration options

    Returns:
        Configured IntegratedA2AAgent instance
    """
    return IntegratedA2AAgent(name=name, description=description, buddy_tools=buddy_tools or [], model=model, **kwargs)
