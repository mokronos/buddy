"""Simple agent implementation with tool calling."""

import os

from dotenv import load_dotenv

load_dotenv()

os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")


class Agent:
    """Simple agent that can interact with LLM and call tools."""

    def __init__(self, name: str, description: str) -> None:
        """Initialize agent with name and description."""
        self.name = name
        self.description = description
