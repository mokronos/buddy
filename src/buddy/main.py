"""
Buddy - Simple Agent with Tool Calling

Main entry point demonstrating the core agent loop.
"""

import asyncio

from buddy.agent.agent import Agent
from buddy.tools.personal_info import PersonalInfoTool


async def main():
    """Main entry point for the simple agent demo."""
    # Create a personal info tool
    personal_info_tool = PersonalInfoTool()

    # Create agent with the tool
    agent = Agent(tools=[personal_info_tool])

    # Run a simple prompt
    print("Running agent with prompt: 'Tell me what you know about Basti'")
    result = await agent.run("Tell me what you know about Basti")
    print(f"Agent result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
