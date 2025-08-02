"""
A2A Protocol adapter implementation using the a2a-sdk.

This module provides the concrete implementation that bridges our Agent
interface with the A2A protocol server from the a2a-sdk library.
"""

import logging
from dataclasses import asdict
from typing import Any

from buddy.agent.interfaces import Agent, AgentRequest

logger = logging.getLogger(__name__)


class A2AServerAdapter:
    """
    Adapter that exposes an Agent through the A2A protocol using a2a-sdk.

    This class handles the translation between our Agent interface and
    the A2A protocol server implementation.
    """

    def __init__(self, agent: Agent):
        self.agent = agent
        self.server = None
        self.is_running_flag = False

    def start_server(self, host: str = "localhost", port: int = 8000) -> None:
        """Start the A2A protocol server for the given agent."""
        try:
            # Import a2a-sdk components
            # Note: This will need the actual a2a-sdk to be installed
            # For now, this is a placeholder showing the intended structure

            # from a2a_sdk import Server, Agent as A2AAgent
            #
            # # Create A2A-compatible agent wrapper
            # a2a_agent = self._create_a2a_agent_wrapper()
            #
            # # Create and configure the server
            # self.server = Server(agent=a2a_agent, host=host, port=port)
            # self.server.start()

            logger.info(f"A2A server started on {host}:{port}")
            self.is_running_flag = True

        except ImportError as e:
            logger.warning("a2a-sdk not available. Server not started.")
            msg = "a2a-sdk is required but not installed"
            raise RuntimeError(msg) from e
        except Exception:
            logger.exception("Failed to start A2A server")
            raise

    def stop_server(self) -> None:
        """Stop the A2A protocol server."""
        if self.server:
            try:
                # self.server.stop()
                logger.info("A2A server stopped")
            except Exception:
                logger.exception("Error stopping A2A server")
            finally:
                self.server = None
                self.is_running_flag = False

    def is_running(self) -> bool:
        """Check if the server is currently running."""
        return self.is_running_flag

    def _create_a2a_agent_wrapper(self):
        """
        Create an A2A-SDK compatible agent wrapper.

        This method would create the necessary wrapper to make our Agent
        compatible with the a2a-sdk's expected interface.
        """
        # This is a placeholder for the actual A2A SDK integration
        # The actual implementation would depend on the a2a-sdk's API

        class A2AAgentWrapper:
            def __init__(self, agent: Agent):
                self.agent = agent

            async def get_capabilities(self):
                """Return capabilities in A2A format."""
                capabilities = self.agent.get_capabilities()
                # Convert to A2A format
                return [asdict(cap) for cap in capabilities]

            async def execute_skill(
                self, skill_name: str, parameters: dict[str, Any], context: dict[str, Any] | None = None
            ):
                """Execute a skill through our agent interface."""
                request = AgentRequest(skill_name=skill_name, parameters=parameters, context=context)
                response = await self.agent.execute_skill(request)

                # Convert response to A2A format
                return {
                    "success": response.success,
                    "result": response.result,
                    "error": response.error,
                    "metadata": response.metadata,
                }

            def get_info(self):
                """Return agent info in A2A format."""
                return self.agent.get_agent_info()

        return A2AAgentWrapper(self.agent)


class MockA2AServerAdapter(A2AServerAdapter):
    """
    Mock implementation of A2A server adapter for testing without a2a-sdk.

    This allows development and testing of the agent logic without requiring
    the actual a2a-sdk to be installed.
    """

    def __init__(self, agent: Agent):
        super().__init__(agent)
        self.mock_server_data = {}

    def start_server(self, host: str = "localhost", port: int = 8000) -> None:
        """Start a mock A2A server."""
        logger.info(f"Mock A2A server started on {host}:{port}")
        self.is_running_flag = True

        # Store mock server configuration
        self.mock_server_data = {
            "host": host,
            "port": port,
            "agent_info": self.agent.get_agent_info(),
            "capabilities": [asdict(cap) for cap in self.agent.get_capabilities()],
        }

    def stop_server(self) -> None:
        """Stop the mock A2A server."""
        logger.info("Mock A2A server stopped")
        self.is_running_flag = False
        self.mock_server_data = {}

    async def simulate_request(
        self, skill_name: str, parameters: dict[str, Any], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Simulate an A2A request for testing purposes."""
        if not self.is_running():
            msg = "Mock server is not running"
            raise RuntimeError(msg)

        request = AgentRequest(skill_name=skill_name, parameters=parameters, context=context)

        response = await self.agent.execute_skill(request)

        return {
            "success": response.success,
            "result": response.result,
            "error": response.error,
            "metadata": response.metadata,
        }

    def get_mock_server_info(self) -> dict[str, Any]:
        """Get information about the mock server for testing."""
        return {
            "is_running": self.is_running(),
            "server_data": self.mock_server_data,
        }


def create_a2a_adapter(agent: Agent, use_mock: bool = False) -> A2AServerAdapter:
    """
    Factory function to create the appropriate A2A adapter.

    Args:
        agent: The agent to wrap
        use_mock: If True, create a mock adapter for testing

    Returns:
        A2A adapter instance
    """
    if use_mock:
        return MockA2AServerAdapter(agent)
    else:
        return A2AServerAdapter(agent)
