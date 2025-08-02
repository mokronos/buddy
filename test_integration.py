"""
Quick test of the integrated A2A agent with LiteLLM and Buddy tools.
"""

import asyncio
import logging

from src.buddy.a2a_agent import (
    DEV_CONFIG,
    ConfigManager,
    create_integrated_agent,
)
from src.buddy.a2a_agent.integrated_example import create_example_buddy_tools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Quick test of the integrated system."""
    logger.info("🧪 Testing Buddy A2A Integration")

    # Check configuration
    config = DEV_CONFIG
    logger.info(f"📋 Model: {config.agent.llm_config.model}")

    # Validate config
    issues = ConfigManager.validate_config(config)
    if issues:
        logger.error(f"❌ Config issues: {issues}")
        return

    # Create tools
    buddy_tools = create_example_buddy_tools()
    logger.info(f"🔧 Created {len(buddy_tools)} tools")

    # Create agent
    agent = create_integrated_agent(
        name="TestAgent",
        description="Test agent for integration",
        buddy_tools=buddy_tools,
        model=config.agent.llm_config.model,
        temperature=0.5,
    )

    logger.info(f"🤖 Created agent with model: {agent.llm_client.model}")

    # Simple test
    from src.buddy.a2a_agent import AgentRequest

    request = AgentRequest(skill_name="use_calculator", parameters={"expression": "2 + 2"})

    response = await agent.execute_skill(request)

    if response.success:
        logger.info(f"✅ Calculator test: {response.result}")
    else:
        logger.error(f"❌ Calculator test failed: {response.error}")

    # Test general query
    request = AgentRequest(skill_name="general_query", parameters={"query": "What tools do you have?"})

    response = await agent.execute_skill(request)

    if response.success:
        logger.info(f"✅ Query test: {response.result[:100]}...")
    else:
        logger.error(f"❌ Query test failed: {response.error}")


if __name__ == "__main__":
    asyncio.run(main())
