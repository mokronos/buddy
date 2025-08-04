"""
Basic agent example demonstrating the simplified core loop.

This example shows how the agent, tools, and LLM components work together.
"""

import asyncio

from buddy.agent.agent import Agent
from buddy.tools.personal_info import PersonalInfoTool


async def main():
    """Run the agent with a real prompt."""
    # Create personal info tool
    personal_info_tool = PersonalInfoTool()

    # Create agent
    agent = Agent(tools=[personal_info_tool])

    # Run agent with prompt
    prompt = "Who is John Hopper? Use the personal_info tool."
    # prompt = "Whats the weather in berlin currently?"
    print(f"Prompt: {prompt}")

    result = await agent.run(prompt)
    print(f"Agent response: {result}")


if __name__ == "__main__":
    asyncio.run(main())
