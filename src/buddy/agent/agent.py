from dotenv import load_dotenv
from langfuse import Langfuse
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from buddy.agent.deps import AgentDeps
from buddy.tools.environment import (
    environment_exec,
    environment_patch_file,
    environment_read_file,
    environment_write_file,
)
from buddy.tools.todo import todoadd, tododelete, todoread, todoupdate
from buddy.tools.web_search import fetch_web_page, web_search

load_dotenv()

langfuse = Langfuse(blocked_instrumentation_scopes=["a2a-python-sdk"])

if not langfuse.auth_check():
    raise RuntimeError("Langfuse authentication failed. Check credentials and host.")

print("Langfuse client is authenticated and ready!")

web_tools = FunctionToolset(
    tools=[
        web_search,
        fetch_web_page,
    ],
)

todo_tools = FunctionToolset(
    tools=[
        todoread,
        todoadd,
        todoupdate,
        tododelete,
    ],
)

environment_tools = FunctionToolset(
    tools=[
        environment_exec,
        environment_read_file,
        environment_write_file,
        environment_patch_file,
    ]
)


def create_agent(name: str, instructions: str) -> Agent:
    return Agent(
        model="openrouter:openrouter/free",
        name=name,
        deps_type=AgentDeps,
        instructions=instructions,
        retries=5,
        # model="google-gla:gemini-2.5-flash",
        # model="google-gla:gemini-2.5-pro",
        # model="google-gla:gemini-2.5-flash-lite",
        toolsets=[web_tools, todo_tools, environment_tools],
        instrument=True,
    )


agent = create_agent(
    "buddy-agent",
    "You are the English Buddy agent. Reply in English only.",
)
second_agent = create_agent(
    "buddy-agent-2",
    "Du bist der deutsche Buddy-Agent. Antworte nur auf Deutsch.",
)

agents = {
    "buddy": agent,
    "buddy-2": second_agent,
}
