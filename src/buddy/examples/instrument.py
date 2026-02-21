from dotenv import load_dotenv

load_dotenv()

import asyncio

from pydantic_ai import Agent, AgentRunResultEvent, AgentStreamEvent, RunContext

from buddy.models import create_codex_model

from langfuse import get_client

langfuse = get_client()

if not langfuse.auth_check():
    raise RuntimeError("Langfuse authentication failed. Check credentials and host.")

print("Langfuse client is authenticated and ready!")

model = create_codex_model(model_name="gpt-5.2")

roulette_agent = Agent(
    model=model,
    deps_type=int,
    instructions=("Use the `roulette_wheel` function to see if the customer has won based on the number they provide."),
)

roulette_agent.instrument_all()


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:
    """check if the square is a winner"""
    return "winner" if square == ctx.deps else "loser"


async def main() -> None:
    success_number = 18
    events: list[AgentStreamEvent | AgentRunResultEvent[str]] = []

    async for event in roulette_agent.run_stream_events("Put my money on square eighteen", deps=success_number):
        events.append(event)

    for event in events:
        print(event)

    if events and isinstance(events[-1], AgentRunResultEvent):
        print(events[-1].result.output)


if __name__ == "__main__":
    asyncio.run(main())
