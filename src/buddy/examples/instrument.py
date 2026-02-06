from phoenix.otel import register

tracer_provider = register(
    project_name="my-llm-app",
    auto_instrument=True,  # automatically instruments OpenAI, LangChain, etc.
)

from dotenv import load_dotenv
load_dotenv()

from pydantic_ai import Agent, RunContext

roulette_agent = Agent(  
    model="google-gla:gemini-2.5-flash",
    deps_type=int,
    output_type=bool,
    system_prompt=(
        'Use the `roulette_wheel` function to see if the '
        'customer has won based on the number they provide.'
    ),
    instrument=True,
)


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:  
    """check if the square is a winner"""
    return 'winner' if square == ctx.deps else 'loser'


# Run the agent
success_number = 18  
result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
print(result.output)  
#> True

result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
print(result.output)
#> False
