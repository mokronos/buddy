from fastapi import FastAPI
from pydantic_ai import Agent


def create_app(agent: Agent):
    return FastAPI(
        title="A2A Server",
        description="A2A Server",
        version="0.1.0",
    )


from dotenv import load_dotenv
from pydantic_ai.toolsets import FunctionToolset

load_dotenv()


def random_tool1(arg1: str, arg2: str):
    import time

    time.sleep(3)
    return f"Result of random long running tool call with args: {arg1} | {arg2}" * 20


tool_set = FunctionToolset(
    tools=[
        random_tool1,
    ],
)

agent = Agent(
    model="google-gla:gemini-2.5-flash",
    toolsets=[tool_set],
)

# app = create_app(agent)
# import uvicorn
# uvicorn.run(app, host="0.0.0.0", port=8000)

app = agent.to_a2a()
