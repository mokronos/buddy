"""
Integrated example demonstrating A2A agent with LiteLLM and Buddy tools.

This example shows how to create and run an A2A agent that uses:
- Your existing LiteLLM implementation
- Existing Buddy tool system
- Google API key from .env
- Full A2A protocol compatibility
"""

import asyncio
import logging

from buddy.agent.a2a_adapter import create_a2a_adapter
from buddy.agent.config import DEV_CONFIG, ConfigManager
from buddy.agent.integrated_agent import create_integrated_agent
from buddy.tools.tool import Tool as BuddyTool

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Example Buddy tools that use your existing Tool class
class CalculatorBuddyTool(BuddyTool):
    """Calculator tool using Buddy Tool interface."""

    def __init__(self):
        super().__init__(name="calculator", description="Perform mathematical calculations and evaluate expressions")

    def run(self, expression: str) -> dict:
        """
        Evaluate a mathematical expression.

        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")

        Returns:
            Dict with expression and result
        """
        import math

        # Safe evaluation with math functions
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }

        try:
            # Allow ^ for exponentiation
            expression = expression.replace("^", "**")
            result = eval(expression, {"__builtins__": {}}, allowed_names)

            return {"expression": expression, "result": result, "type": type(result).__name__}
        except Exception as e:
            return {"expression": expression, "error": str(e), "result": None}


class WeatherBuddyTool(BuddyTool):
    """Mock weather tool using Buddy Tool interface."""

    def __init__(self):
        super().__init__(name="weather", description="Get current weather information for a location")

    def run(self, location: str) -> dict:
        """
        Get weather for a location.

        Args:
            location: City or location name

        Returns:
            Dict with weather information
        """
        # Mock weather data
        import random

        temperatures = [15, 18, 22, 25, 28, 31, 35]
        conditions = ["sunny", "cloudy", "partly cloudy", "rainy", "windy"]

        return {
            "location": location,
            "temperature": random.choice(temperatures),
            "condition": random.choice(conditions),
            "humidity": random.randint(30, 80),
            "source": "mock_weather_api",
        }


class NoteBuddyTool(BuddyTool):
    """Simple note-taking tool using Buddy Tool interface."""

    def __init__(self):
        super().__init__(name="notes", description="Save and retrieve notes")
        self._notes = {}

    def run(self, action: str, note_id: str | None = None, content: str | None = None) -> dict:
        """
        Manage notes.

        Args:
            action: Action to perform (save, get, list, delete)
            note_id: ID of the note (required for save, get, delete)
            content: Note content (required for save)

        Returns:
            Dict with action result
        """
        if action == "save":
            if not note_id or not content:
                return {"error": "note_id and content required for save"}

            self._notes[note_id] = content
            return {"action": "save", "note_id": note_id, "content": content, "saved": True}

        elif action == "get":
            if not note_id:
                return {"error": "note_id required for get"}

            content = self._notes.get(note_id)
            return {"action": "get", "note_id": note_id, "content": content, "found": content is not None}

        elif action == "list":
            return {"action": "list", "notes": list(self._notes.keys()), "count": len(self._notes)}

        elif action == "delete":
            if not note_id:
                return {"error": "note_id required for delete"}

            deleted = self._notes.pop(note_id, None)
            return {"action": "delete", "note_id": note_id, "deleted": deleted is not None, "content": deleted}

        else:
            return {"error": f"Unknown action: {action}"}


def create_example_buddy_tools() -> list[BuddyTool]:
    """Create a list of example Buddy tools."""
    return [CalculatorBuddyTool(), WeatherBuddyTool(), NoteBuddyTool()]


async def test_integrated_agent():
    """Test the integrated A2A agent with real LiteLLM integration."""
    logger.info("🚀 Testing integrated A2A agent with LiteLLM and Buddy tools")

    # Create Buddy tools
    buddy_tools = create_example_buddy_tools()
    logger.info(f"📝 Created {len(buddy_tools)} Buddy tools: {[t.name for t in buddy_tools]}")

    # Load configuration
    config = DEV_CONFIG
    logger.info(f"⚙️ Using model: {config.agent.llm_config.model}")

    # Validate configuration
    issues = ConfigManager.validate_config(config)
    if issues:
        logger.error(f"❌ Configuration issues: {issues}")
        return

    # Create integrated agent
    agent = create_integrated_agent(
        name=config.agent.name,
        description=config.agent.description,
        buddy_tools=buddy_tools,
        model=config.agent.llm_config.model,
        temperature=config.agent.llm_config.temperature,
    )

    logger.info(f"🤖 Created agent: {agent.name}")
    logger.info(f"🔧 LLM Model: {agent.llm_client.model}")

    # Test basic functionality
    await test_agent_capabilities(agent)

    # Test A2A integration
    await test_a2a_integration(agent, config)


async def test_agent_capabilities(agent):
    """Test the agent's basic capabilities."""
    logger.info("\n=== Testing Agent Capabilities ===")

    test_cases = [
        {
            "skill": "general_query",
            "params": {"query": "What tools do you have available?"},
            "description": "Tool discovery",
        },
        {
            "skill": "use_calculator",
            "params": {"expression": "sqrt(144) + 5 * 3"},
            "description": "Calculator tool test",
        },
        {"skill": "use_weather", "params": {"location": "San Francisco"}, "description": "Weather tool test"},
        {
            "skill": "use_notes",
            "params": {"action": "save", "note_id": "test1", "content": "This is a test note from A2A agent"},
            "description": "Notes save test",
        },
        {"skill": "use_notes", "params": {"action": "get", "note_id": "test1"}, "description": "Notes retrieve test"},
        {
            "skill": "tool_execution",
            "params": {"task": "Calculate the area of a circle with radius 5 and save the result as a note"},
            "description": "Multi-tool coordination",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n🧪 Test {i}: {test_case['description']}")

        try:
            from buddy.agent.interfaces import AgentRequest

            request = AgentRequest(skill_name=test_case["skill"], parameters=test_case["params"])

            response = await agent.execute_skill(request)

            if response.success:
                logger.info(f"✅ Success: {response.result}")
            else:
                logger.error(f"❌ Failed: {response.error}")

        except Exception:
            logger.exception("💥 Exception occurred")

        await asyncio.sleep(1)  # Small delay between tests


async def test_a2a_integration(agent, config):
    """Test A2A protocol integration."""
    logger.info("\n=== Testing A2A Integration ===")

    # Create A2A adapter
    adapter = create_a2a_adapter(agent, use_mock=config.a2a.use_mock)

    try:
        # Start server
        adapter.start_server(config.a2a.host, config.a2a.port)
        logger.info(f"🌐 A2A server started on {config.a2a.host}:{config.a2a.port}")

        if config.a2a.use_mock:
            # Test mock interactions
            logger.info("🔧 Testing mock A2A interactions...")

            test_request = await adapter.simulate_request(
                skill_name="use_calculator", parameters={"expression": "2^8 + 10"}
            )

            logger.info(f"📊 Mock test result: {test_request}")
        else:
            logger.info("🔗 Real A2A server running. Use A2A Inspector to test.")
            # Keep server running for manual testing
            logger.info("Press Ctrl+C to stop...")
            try:
                while adapter.is_running():
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")

    finally:
        adapter.stop_server()
        logger.info("🔚 A2A server stopped")


async def demonstrate_model_switching():
    """Demonstrate switching between different models."""
    logger.info("\n=== Testing Model Switching ===")

    available_models = ConfigManager.get_available_models()
    logger.info(f"📋 Available models: {list(available_models.keys())}")

    for model_name, model_info in available_models.items():
        if model_info.get("available", False):
            logger.info(f"🔄 Testing with {model_name}: {model_info['model']}")

            try:
                agent = create_integrated_agent(
                    name=f"TestAgent-{model_name}",
                    description="Test agent for model switching",
                    buddy_tools=[CalculatorBuddyTool()],
                    model=model_info["model"],
                    temperature=0.5,
                )

                from buddy.agent.interfaces import AgentRequest

                request = AgentRequest(skill_name="general_query", parameters={"query": "What is 7 * 8?"})

                response = await agent.execute_skill(request)
                logger.info(f"✅ {model_name}: {response.result[:100]}...")

            except Exception:
                logger.exception(f"❌ {model_name} failed")

            break  # Test just one available model for demo


async def main():
    """Main entry point for the integrated example."""
    logger.info("🎯 Starting Buddy A2A Integration Demo")

    try:
        # Test integrated agent
        await test_integrated_agent()

        # Demonstrate model switching
        await demonstrate_model_switching()

        logger.info("🎉 Integration demo completed successfully!")

    except Exception:
        logger.exception("💥 Demo failed")
        raise


if __name__ == "__main__":
    asyncio.run(main())
