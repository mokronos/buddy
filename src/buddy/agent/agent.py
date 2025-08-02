"""
Core agent implementation with LLM loop and tool support.
"""

import json
from dataclasses import asdict
from typing import Any

from buddy.agent.interfaces import Agent, AgentRequest, AgentResponse, Capability, Skill, SkillType, Tool


class LLMAgent(Agent):
    """
    Core agent implementation with LLM loop and tool integration.

    This agent can execute skills by using an LLM to reason about requests
    and orchestrate tool usage to complete tasks.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        llm_client: Any | None = None,
        tools: list[Tool] | None = None,
        system_prompt: str | None = None,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.llm_client = llm_client
        self.tools = tools or []
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Create a mapping of tool names to tools for quick lookup
        self.tool_map = {tool.get_name(): tool for tool in self.tools}

    def _default_system_prompt(self) -> str:
        """Generate a default system prompt based on available tools."""
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.get_name()}: {tool.get_description()}")

        tools_section = "\n".join(tool_descriptions) if tool_descriptions else "No tools available."

        return f"""You are {self.name}, {self.description}

Available tools:
{tools_section}

When executing skills:
1. Analyze the request and determine what needs to be done
2. Use available tools as needed to complete the task
3. Provide a clear, helpful response based on the results
4. If you need to use a tool, specify the tool name and parameters in your response

Respond in a helpful and concise manner."""

    def get_capabilities(self) -> list[Capability]:
        """Return the capabilities this agent provides."""
        skills = [
            Skill(
                name="general_query",
                description="Answer general questions and provide information",
                skill_type=SkillType.QUERY,
                parameters={
                    "query": {"type": "string", "description": "The question or request"},
                    "context": {"type": "object", "description": "Additional context", "required": False},
                },
                examples=["What is the weather like?", "Explain quantum computing", "Help me with a task"],
            ),
            Skill(
                name="tool_execution",
                description="Execute tasks using available tools",
                skill_type=SkillType.ACTION,
                parameters={
                    "task": {"type": "string", "description": "The task to perform"},
                    "tool_params": {"type": "object", "description": "Parameters for tools", "required": False},
                },
                examples=["Search for information", "Process data", "Perform calculations"],
            ),
        ]

        # Add tool-specific skills
        for tool in self.tools:
            skills.append(
                Skill(
                    name=f"use_{tool.get_name()}",
                    description=f"Use the {tool.get_name()} tool: {tool.get_description()}",
                    skill_type=SkillType.ACTION,
                    parameters=tool.get_parameters_schema(),
                )
            )

        return [
            Capability(
                name=self.name,
                description=self.description,
                version=self.version,
                skills=skills,
            )
        ]

    async def execute_skill(self, request: AgentRequest) -> AgentResponse:
        """Execute a specific skill with the given request."""
        try:
            # Route to appropriate handler based on skill name
            if request.skill_name == "general_query":
                return await self._handle_general_query(request)
            elif request.skill_name == "tool_execution":
                return await self._handle_tool_execution(request)
            elif request.skill_name.startswith("use_"):
                tool_name = request.skill_name[4:]  # Remove "use_" prefix
                return await self._handle_direct_tool_use(tool_name, request)
            else:
                return AgentResponse(
                    success=False,
                    result=None,
                    error=f"Unknown skill: {request.skill_name}",
                )
        except Exception as e:
            return AgentResponse(
                success=False,
                result=None,
                error=f"Error executing skill {request.skill_name}: {e!s}",
            )

    async def _handle_general_query(self, request: AgentRequest) -> AgentResponse:
        """Handle general query requests."""
        query = request.parameters.get("query", "")
        context = request.parameters.get("context", {})

        if not self.llm_client:
            return AgentResponse(
                success=False,
                result=None,
                error="No LLM client configured",
            )

        # Prepare the prompt with context
        prompt = f"Query: {query}"
        if context:
            prompt += f"\nContext: {json.dumps(context, indent=2)}"

        try:
            # Use LLM to process the query
            response = await self._call_llm(prompt)

            return AgentResponse(
                success=True,
                result=response,
                metadata={"skill": "general_query", "query": query},
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                result=None,
                error=f"LLM error: {e!s}",
            )

    async def _handle_tool_execution(self, request: AgentRequest) -> AgentResponse:
        """Handle tool execution requests with LLM reasoning."""
        task = request.parameters.get("task", "")
        tool_params = request.parameters.get("tool_params", {})

        if not self.llm_client:
            return AgentResponse(
                success=False,
                result=None,
                error="No LLM client configured for tool execution reasoning",
            )

        # Use LLM to determine which tools to use and how
        prompt = f"""Task: {task}
Available tools: {[tool.get_name() for tool in self.tools]}
Tool parameters provided: {json.dumps(tool_params, indent=2)}

Determine which tool(s) to use and with what parameters to complete this task.
Respond with a JSON object containing:
{{
    "tool_name": "name_of_tool_to_use",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "reasoning": "why this tool and these parameters"
}}

If multiple tools are needed, respond with an array of such objects."""

        try:
            llm_response = await self._call_llm(prompt)

            # Parse LLM response to extract tool usage instructions
            tool_instructions = self._parse_tool_instructions(llm_response)

            # Execute the tools
            results = []
            for instruction in tool_instructions:
                tool_result = await self._execute_tool(instruction["tool_name"], instruction["parameters"])
                results.append({
                    "tool": instruction["tool_name"],
                    "result": tool_result,
                    "reasoning": instruction.get("reasoning", ""),
                })

            return AgentResponse(
                success=True,
                result=results,
                metadata={"skill": "tool_execution", "task": task},
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                result=None,
                error=f"Tool execution error: {e!s}",
            )

    async def _handle_direct_tool_use(self, tool_name: str, request: AgentRequest) -> AgentResponse:
        """Handle direct tool usage requests."""
        if tool_name not in self.tool_map:
            return AgentResponse(
                success=False,
                result=None,
                error=f"Tool not found: {tool_name}",
            )

        try:
            result = await self._execute_tool(tool_name, request.parameters)
            return AgentResponse(
                success=True,
                result=result,
                metadata={"skill": f"use_{tool_name}", "tool": tool_name},
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                result=None,
                error=f"Error using tool {tool_name}: {e!s}",
            )

    async def _execute_tool(self, tool_name: str, parameters: dict[str, Any]) -> Any:
        """Execute a specific tool with given parameters."""
        if tool_name not in self.tool_map:
            msg = f"Tool not found: {tool_name}"
            raise ValueError(msg)

        tool = self.tool_map[tool_name]
        return await tool.execute(parameters)

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt."""
        if not self.llm_client:
            msg = "No LLM client configured"
            raise ValueError(msg)

        # This is a placeholder - actual implementation depends on your LLM client
        # For now, return a mock response
        return f"LLM response to: {prompt[:100]}..."

    def _parse_tool_instructions(self, llm_response: str) -> list[dict[str, Any]]:
        """Parse LLM response to extract tool usage instructions."""
        try:
            # Try to parse as JSON
            parsed = json.loads(llm_response)

            # Handle both single instruction and array of instructions
            if isinstance(parsed, dict):
                return [parsed]
            elif isinstance(parsed, list):
                return parsed
            else:
                msg = "Invalid instruction format"
                raise TypeError(msg)
        except json.JSONDecodeError:
            # Fallback: return a basic instruction
            return [
                {
                    "tool_name": "unknown",
                    "parameters": {},
                    "reasoning": "Could not parse LLM response",
                }
            ]

    def get_agent_info(self) -> dict[str, Any]:
        """Return basic information about this agent."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": [asdict(cap) for cap in self.get_capabilities()],
            "tools": [tool.get_name() for tool in self.tools],
        }
