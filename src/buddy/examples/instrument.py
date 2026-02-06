from dotenv import load_dotenv

load_dotenv()

import os
from typing import Any, cast

from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModelName, OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from langfuse import get_client

langfuse = get_client()

# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

default_headers = {
    "originator": "opencode",
    "Openai-Intent": "conversation-edits",
    "User-Agent": "opencode/0.0.0",
}

if account_id := os.getenv("ACCOUNT_ID"):
    default_headers["ChatGPT-Account-Id"] = account_id

openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_ACCESS_TOKEN"),
    base_url="https://chatgpt.com/backend-api/codex",
    default_headers=default_headers,
)

model_name: OpenAIModelName = cast(OpenAIModelName, "gpt-5.2")
model = OpenAIResponsesModel(model_name, provider=OpenAIProvider(openai_client=openai_client))

model_settings: OpenAIResponsesModelSettings = {"openai_store": False}

roulette_agent = Agent(
    # model="google-gla:gemini-2.5-flash",
    model=model,
    deps_type=int,
    # output_type=bool,
    model_settings=cast(Any, model_settings),
    instructions=("Use the `roulette_wheel` function to see if the customer has won based on the number they provide."),
)

roulette_agent.instrument_all()


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:
    """check if the square is a winner"""
    return "winner" if square == ctx.deps else "loser"


# Run the agent
success_number = 18
result = roulette_agent.run_sync("Put my money on square eighteen", deps=success_number)
print(result.output)
