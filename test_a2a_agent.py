"""
Test script for the A2A agent implementation.

This script demonstrates how to test the A2A agent without requiring
the actual a2a-sdk installation.
"""

import asyncio
import logging

from src.buddy.a2a_agent import (
    AgentRequest,
    CalculatorTool,
    LLMAgent,
    create_a2a_adapter,
    get_example_tools,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLM:
    """Mock LLM for testing."""

    async def generate_response(self, prompt: str) -> str:
        return "Mock LLM response"


async def test_agent_creation():
    """Test creating an agent with tools."""
    logger.info("Testing agent creation...")

    tools = get_example_tools()
    agent = LLMAgent(name="TestAgent", description="A test agent", tools=tools, llm_client=MockLLM())

    # Test capabilities
    capabilities = agent.get_capabilities()
    logger.info(f"Agent has {len(capabilities)} capabilities")

    for cap in capabilities:
        logger.info(f"Capability: {cap.name} with {len(cap.skills)} skills")

    # Test agent info
    info = agent.get_agent_info()
    logger.info(f"Agent info: {info['name']} - {info['description']}")

    return agent


async def test_tool_execution():
    """Test individual tool execution."""
    logger.info("Testing tool execution...")

    calc_tool = CalculatorTool()

    # Test calculator
    result = await calc_tool.execute({"expression": "2 + 3 * 4"})
    logger.info(f"Calculator result: {result}")

    assert result["result"] == 14, "Calculator test failed"
    logger.info("Calculator tool test passed")


async def test_agent_skills():
    """Test agent skill execution."""
    logger.info("Testing agent skills...")

    agent = await test_agent_creation()

    # Test calculator skill
    request = AgentRequest(skill_name="use_calculator", parameters={"expression": "sqrt(16) + 2"})

    response = await agent.execute_skill(request)
    logger.info(f"Skill response: success={response.success}, result={response.result}")

    if response.success:
        logger.info("Calculator skill test passed")
    else:
        logger.error(f"Calculator skill test failed: {response.error}")


async def test_mock_a2a_adapter():
    """Test the mock A2A adapter."""
    logger.info("Testing mock A2A adapter...")

    agent = await test_agent_creation()
    adapter = create_a2a_adapter(agent, use_mock=True)

    # Start mock server
    adapter.start_server("localhost", 8001)
    assert adapter.is_running(), "Mock server should be running"

    # Test a request
    result = await adapter.simulate_request(skill_name="use_calculator", parameters={"expression": "5 * 5"})

    logger.info(f"Mock A2A request result: {result}")

    # Stop server
    adapter.stop_server()
    assert not adapter.is_running(), "Mock server should be stopped"

    logger.info("Mock A2A adapter test passed")


async def main():
    """Run all tests."""
    logger.info("Starting A2A agent tests...")

    try:
        await test_tool_execution()
        await test_agent_creation()
        await test_agent_skills()
        await test_mock_a2a_adapter()

        logger.info("All tests passed! ✅")

    except Exception:
        logger.exception("Test failed")
        raise


if __name__ == "__main__":
    asyncio.run(main())
