"""
Core agent loop implementation.

This module implements the main agent loop that provides continuous
interaction between an LLM and its environment through tools.
"""

from typing import Any

from buddy.agent.interfaces import Agent, AgentRequest
from buddy.llm.context import ContextManager
from buddy.llm.llm_client import LiteLLMClient


class AgentLoop:
    """
    Core agent loop that manages LLM interaction cycles.

    The loop handles:
    - LLM requests and responses
    - Tool execution
    - Context management
    - Human-in-the-loop interactions
    - State persistence
    """

    def __init__(
        self,
        agent: Agent,
        llm_client: LiteLLMClient,
        context_manager: ContextManager | None = None,
        max_iterations: int = 50,
    ):
        """Initialize the agent loop."""
        self.agent = agent
        self.llm_client = llm_client
        self.context_manager = context_manager or ContextManager()
        self.max_iterations = max_iterations
        self.running = False
        self.current_iteration = 0

    async def run(self, initial_prompt: str) -> list[dict[str, Any]]:
        """
        Run the agent loop with an initial prompt.

        Returns a list of all interactions in the loop.
        """
        self.running = True
        self.current_iteration = 0
        interactions = []

        # Initialize context with the initial prompt
        self.context_manager.add_message("user", initial_prompt)

        while self.running and self.current_iteration < self.max_iterations:
            try:
                # Get current context for LLM
                context = self.context_manager.get_context_for_llm()

                # Generate LLM response
                llm_response = await self.llm_client.generate_with_tools(
                    prompt="",  # Prompt is in context
                    messages=context["messages"],
                    tools=context.get("tools", []),
                )

                interaction = {
                    "iteration": self.current_iteration,
                    "llm_response": llm_response,
                    "tool_results": [],
                    "status": "running",
                }

                # Add LLM response to context
                self.context_manager.add_message("assistant", llm_response.get("content", ""))

                # Execute any tool calls
                if llm_response.get("tool_calls"):
                    for tool_call in llm_response["tool_calls"]:
                        tool_result = await self._execute_tool_call(tool_call)
                        interaction["tool_results"].append(tool_result)

                        # Add tool result to context
                        self.context_manager.add_tool_result(tool_call["name"], tool_call["arguments"], tool_result)

                # Check if we should continue
                if self._should_stop(llm_response, interaction):
                    interaction["status"] = "completed"
                    self.running = False

                interactions.append(interaction)
                self.current_iteration += 1

                # Manage context size
                self.context_manager.manage_context_size()

            except Exception as e:
                error_interaction = {"iteration": self.current_iteration, "error": str(e), "status": "error"}
                interactions.append(error_interaction)
                break

        return interactions

    async def _execute_tool_call(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Execute a single tool call."""
        try:
            # Create agent request from tool call
            request = AgentRequest(skill_name=f"use_{tool_call['name']}", parameters=tool_call["arguments"])

            # Execute through agent
            response = await self.agent.execute_skill(request)

            return {
                "tool_name": tool_call["name"],
                "arguments": tool_call["arguments"],
                "success": response.success,
                "result": response.result,
                "error": response.error,
            }

        except Exception as e:
            return {
                "tool_name": tool_call["name"],
                "arguments": tool_call["arguments"],
                "success": False,
                "result": None,
                "error": str(e),
            }

    def _should_stop(self, llm_response: dict[str, Any], interaction: dict[str, Any]) -> bool:
        """Determine if the agent loop should stop."""
        # Stop if LLM indicates completion
        if llm_response.get("finish_reason") == "stop":
            content = llm_response.get("content", "").lower()
            if any(phrase in content for phrase in ["task complete", "finished", "done"]):
                return True

        # Stop if no tool calls and no meaningful content
        if not llm_response.get("tool_calls") and not llm_response.get("content", "").strip():
            return True

        # Stop if tool execution failed critically
        for tool_result in interaction["tool_results"]:
            if not tool_result["success"] and "critical" in tool_result.get("error", "").lower():
                return True

        return False

    async def stop(self):
        """Stop the agent loop."""
        self.running = False

    def get_status(self) -> dict[str, Any]:
        """Get current status of the agent loop."""
        return {
            "running": self.running,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "context_size": self.context_manager.get_context_size(),
        }
