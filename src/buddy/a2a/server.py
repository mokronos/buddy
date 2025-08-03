"""
A2A server implementation that wraps the core agent.

This server exposes the Buddy agent through the Agent-to-Agent protocol,
enabling standardized communication with A2A clients.
"""

import asyncio

from buddy.agent.interfaces import Agent


class A2AServer:
    """A2A protocol server that wraps the core agent."""

    def __init__(self, agent: Agent, host: str = "localhost", port: int = 8000):
        """Initialize the A2A server."""
        self.agent = agent
        self.host = host
        self.port = port
        self.running = False

    async def start(self):
        """Start the A2A server."""
        self.running = True
        print(f"A2A server starting on {self.host}:{self.port}")

        # TODO: Implement actual A2A protocol server
        # For now, just simulate a running server
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop the A2A server."""
        self.running = False
        print("A2A server stopped")

    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.running
