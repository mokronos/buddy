"""
Basic agent example implemented with PydanticAI.

This example demonstrates a minimal agent with a single tool implemented via
PydanticAI's @agent.tool decorator. It requires an `OPENAI_API_KEY` in the
environment to run.
"""

from __future__ import annotations

import asyncio
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, MCPServerStreamableHTTP, ToolResult

load_dotenv()


class AgentContext(BaseModel):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str


agent: Agent[Any, Any] = Agent(
    model="google-gla:gemini-2.5-flash",
    deps_type=AgentContext,
    system_prompt=("You are a helpful assistant."),
)


@agent.tool
def personal_info(ctx: RunContext[Any], name: str) -> str:
    """Retrieve personal information about a person by name.

    The database is intentionally tiny for demonstration purposes.
    """
    people_info: dict[str, str] = {
        "basti": "29 years old, works as a data scientist in Nuremberg, Germany, and has a sister named Caro.",
        "john": "29 years old, works as a data scientist in Nuremberg, Germany, and has a sister named Caro.",
        "john hopper": "29 years old, works as a data scientist in Nuremberg, Germany, and has a sister named Caro.",
    }

    normalized_name = name.lower().strip()

    # Basic normalization to map variants like "john hopper" -> "john"
    alias_map: dict[str, str] = {
        "john hopper": "john",
    }
    normalized_key = alias_map.get(normalized_name, normalized_name)

    return people_info.get(normalized_key, f"No information available for '{name}'")


async def process_tool_call(
    ctx: RunContext[int],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    return await call_tool(name, tool_args, {"deps": ctx.deps})


async def main() -> None:
    # prompt = "Play your favorite song. Imagine you have one. Please just play one. Don't tell me you don't have one. Play it on my pc."
    prompt = "Please list all the available spotify devices."
    print(f"Prompt: {prompt}")

    server = MCPServerStreamableHTTP(url="http://127.0.0.1:8000/mcp", process_tool_call=process_tool_call)

    SPOTIPY_CLIENT_ID = "b2e6ae7d55254a89a48c29ecaa60ff88"
    SPOTIPY_CLIENT_SECRET = "e494424000e540efa9c472c11162193c"
    SPOTIPY_REDIRECT_URI = "http://127.0.0.1:9090"

    deps = AgentContext(
        spotify_client_id=SPOTIPY_CLIENT_ID,
        spotify_client_secret=SPOTIPY_CLIENT_SECRET,
        spotify_redirect_uri=SPOTIPY_REDIRECT_URI,
    )

    agent.run()

    async with agent.iter(prompt, toolsets=[server], deps=deps) as agent_run:
        async for node in agent_run:
            print(node)


if __name__ == "__main__":
    asyncio.run(main())
