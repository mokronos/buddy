from phoenix.otel import register

tracer_provider = register(
    project_name="my-llm-app",
    auto_instrument=False,
    set_global_tracer_provider=False,
)

from dotenv import load_dotenv

load_dotenv()

import os

from pydantic_ai import Agent, InstrumentationSettings, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIResponsesModel("gpt-5.2", provider=OpenAIProvider(api_key=os.getenv("OPENAI_ACCESS_TOKEN"), base_url="https://chatgpt.com/backend-api/codex/responses"))

roulette_agent = Agent(
    # model="google-gla:gemini-2.5-flash",
    model=model,
    deps_type=int,
    output_type=bool,
    system_prompt=(
        "Use the `roulette_wheel` function to see if the customer has won based on the number they provide."
    ),
    instrument=InstrumentationSettings(tracer_provider=tracer_provider),
)


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:
    """check if the square is a winner"""
    return "winner" if square == ctx.deps else "loser"


# Run the agent
success_number = 18
result = roulette_agent.run_sync("Put my money on square eighteen", deps=success_number)
print(result.output)
# > True
