"""
Example A2A agent server implementation.

This script demonstrates how to create and run an A2A-compatible agent
that can be tested with the A2A inspector.
"""

import asyncio
import logging

from .a2a_adapter import create_a2a_adapter
from .agent import LLMAgent
from .example_tools import get_example_tools

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MockLLMClient:
    """
    Mock LLM client for demonstration purposes.

    In a real implementation, this would be replaced with an actual
    LLM client (e.g., OpenAI, Anthropic, local model, etc.)
    """

    async def generate_response(self, prompt: str) -> str:
        """Generate a mock response based on the prompt."""
        # Simple pattern matching for demonstration
        if "calculator" in prompt.lower() or "math" in prompt.lower():
            return """{"tool_name": "calculator", "parameters": {"expression": "2 + 2"}, "reasoning": "User seems to want a mathematical calculation"}"""

        elif "text" in prompt.lower() and "count" in prompt.lower():
            return """{"tool_name": "text_processor", "parameters": {"text": "sample text", "operation": "word_count"}, "reasoning": "User wants text analysis"}"""

        elif "time" in prompt.lower():
            return """{"tool_name": "time_tool", "parameters": {"action": "current_time"}, "reasoning": "User wants current time information"}"""

        else:
            return "I understand your request. Based on the available tools, I can help with calculations, text processing, time operations, and data storage."


async def create_example_agent() -> LLMAgent:
    """Create an example A2A agent with tools and mock LLM."""

    # Create mock LLM client
    llm_client = MockLLMClient()

    # Get example tools
    tools = get_example_tools()

    # Create the agent
    agent = LLMAgent(
        name="ExampleA2AAgent",
        description="An example agent demonstrating A2A protocol compatibility with tool support",
        version="1.0.0",
        llm_client=llm_client,
        tools=tools,
        system_prompt="""You are ExampleA2AAgent, a helpful assistant with access to various tools.

Available tools:
- calculator: Perform mathematical calculations
- text_processor: Process and analyze text
- time_tool: Get time information and perform time calculations
- data_storage: Store and retrieve data

When a user asks for something:
1. Determine which tool(s) would be most helpful
2. Use the appropriate tool with correct parameters
3. Provide a clear response based on the results

Always be helpful and accurate in your responses.""",
    )

    return agent


async def run_example_server(host: str = "localhost", port: int = 8000, use_mock: bool = True):
    """Run the example A2A agent server."""

    logger.info("Creating example A2A agent...")
    agent = await create_example_agent()

    logger.info("Setting up A2A adapter...")
    adapter = create_a2a_adapter(agent, use_mock=use_mock)

    try:
        logger.info(f"Starting A2A server on {host}:{port}")
        adapter.start_server(host=host, port=port)

        # Display agent information
        agent_info = agent.get_agent_info()
        logger.info(f"Agent: {agent_info['name']} v{agent_info['version']}")
        logger.info(f"Description: {agent_info['description']}")
        logger.info(f"Available tools: {', '.join(agent_info['tools'])}")

        if use_mock:
            logger.info("Running with mock A2A adapter (for testing without a2a-sdk)")
            await demo_mock_interactions(adapter)
        else:
            logger.info("Server running with real A2A SDK. Use A2A Inspector to test.")
            # Keep the server running
            while adapter.is_running():
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Error running server: {e}")
    finally:
        logger.info("Stopping A2A server...")
        adapter.stop_server()


async def demo_mock_interactions(adapter):
    """Demonstrate the agent's capabilities using the mock adapter."""

    logger.info("\n=== Demo: Testing agent interactions ===")

    # Test cases
    test_cases = [
        {
            "skill": "general_query",
            "params": {"query": "What can you help me with?"},
            "description": "General capability query",
        },
        {
            "skill": "use_calculator",
            "params": {"expression": "sqrt(16) + 5 * 3"},
            "description": "Mathematical calculation",
        },
        {
            "skill": "use_text_processor",
            "params": {"text": "Hello World! This is a test message.", "operation": "analyze"},
            "description": "Text analysis",
        },
        {"skill": "use_time_tool", "params": {"action": "current_time"}, "description": "Current time request"},
        {
            "skill": "use_data_storage",
            "params": {"action": "store", "key": "test_data", "value": {"message": "Hello A2A!"}},
            "description": "Data storage",
        },
        {
            "skill": "use_data_storage",
            "params": {"action": "retrieve", "key": "test_data"},
            "description": "Data retrieval",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest {i}: {test_case['description']}")
        logger.info(f"Skill: {test_case['skill']}")
        logger.info(f"Parameters: {test_case['params']}")

        try:
            result = await adapter.simulate_request(skill_name=test_case["skill"], parameters=test_case["params"])

            logger.info(f"Success: {result['success']}")
            if result["success"]:
                logger.info(f"Result: {result['result']}")
            else:
                logger.error(f"Error: {result['error']}")

        except Exception as e:
            logger.error(f"Exception during test: {e}")

        await asyncio.sleep(0.5)  # Small delay between tests

    logger.info("\n=== Demo completed ===")


async def main():
    """Main entry point for the example server."""
    import argparse

    parser = argparse.ArgumentParser(description="Run example A2A agent server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--no-mock", action="store_true", help="Use real A2A SDK instead of mock")

    args = parser.parse_args()

    await run_example_server(host=args.host, port=args.port, use_mock=not args.no_mock)


if __name__ == "__main__":
    asyncio.run(main())
