import os
from time import sleep
from typing import Any, NoReturn, cast

from dotenv import load_dotenv
from langfuse import Langfuse
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from buddy.runtime.deps import AgentDeps
from buddy.runtime.tools.environment import (
    environment_exec,
    environment_patch_file,
    environment_read_file,
    environment_write_file,
)
from buddy.runtime.tools.todo import todoadd, tododelete, todoread, todoupdate
from buddy.runtime.tools.web_search import fetch_web_page, web_search

load_dotenv()


def _raise_langfuse_auth_error() -> NoReturn:
    raise RuntimeError("Langfuse authentication failed. Check credentials and host.")


def _is_langfuse_ready() -> bool:
    require_langfuse = os.environ.get("BUDDY_REQUIRE_LANGFUSE", "false").lower() == "true"
    has_keys = bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))

    if not has_keys:
        if require_langfuse:
            _raise_langfuse_auth_error()
        print("Langfuse credentials missing; continuing with instrumentation disabled.")
        return False

    last_error: Exception | None = None
    for _ in range(5):
        try:
            langfuse = Langfuse(blocked_instrumentation_scopes=["a2a-python-sdk"])
            if langfuse.auth_check():
                print("Langfuse client is authenticated and ready!")
                return True
        except Exception as error:
            last_error = error
        sleep(1)

    if require_langfuse:
        if last_error is not None:
            raise RuntimeError(f"Langfuse unavailable ({last_error})") from last_error
        _raise_langfuse_auth_error()

    if last_error is not None:
        print(f"Langfuse unavailable during startup ({last_error}); continuing with instrumentation enabled.")
    else:
        print("Langfuse auth check failed during startup; continuing with instrumentation enabled.")
    return True


langfuse_ready = _is_langfuse_ready()
if langfuse_ready:
    Agent.instrument_all()

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


def create_agent(
    name: str,
    instructions: str,
    *,
    model: str = "openrouter:openrouter/free",
    enable_web_search: bool = True,
    enable_todo: bool = True,
    enable_environment: bool = True,
) -> Agent[AgentDeps, str]:
    if enable_web_search and enable_todo and enable_environment:
        toolsets = [web_tools, todo_tools, environment_tools]
    elif enable_web_search and enable_todo:
        toolsets = [web_tools, todo_tools]
    elif enable_web_search and enable_environment:
        toolsets = [web_tools, environment_tools]
    elif enable_todo and enable_environment:
        toolsets = [todo_tools, environment_tools]
    elif enable_web_search:
        toolsets = [web_tools]
    elif enable_todo:
        toolsets = [todo_tools]
    elif enable_environment:
        toolsets = [environment_tools]
    else:
        toolsets = []

    return Agent(
        model=model,
        name=name,
        deps_type=AgentDeps,
        instructions=instructions,
        retries=5,
        # model="google-gla:gemini-2.5-flash",
        # model="google-gla:gemini-2.5-pro",
        # model="google-gla:gemini-2.5-flash-lite",
        toolsets=cast(Any, toolsets),
        instrument=langfuse_ready,
    )


agent = create_agent(
    "buddy-agent",
    "You are the English Buddy agent. Reply in English only.",
)

agents = {
    "buddy": agent,
}
