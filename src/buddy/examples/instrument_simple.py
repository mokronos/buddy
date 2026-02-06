from dotenv import load_dotenv

load_dotenv()

from pydantic_ai import Agent, RunContext

from langfuse import get_client

langfuse = get_client()

# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

Agent.instrument_all()

roulette_agent = Agent(
    model="google-gla:gemini-2.5-flash-lite",
    deps_type=int,
    instructions=("Use the `roulette_wheel` function to see if the customer has won based on the number they provide."),
    instrument=True,
)


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:
    """check if the square is a winner"""
    return "winner" if square == ctx.deps else "loser"


# Run the agent
success_number = 18
result = roulette_agent.run_sync("Put my money on square eighteen", deps=success_number)
# print(result.get_output())
print(result.output)
for message in result.all_messages():
    print(message)
# > True

langfuse.flush()
