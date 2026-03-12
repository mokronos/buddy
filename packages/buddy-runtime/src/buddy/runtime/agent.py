import logging
import os
from time import sleep
from typing import Any, NoReturn, cast

from buddy.runtime.tools.todo import todoadd, tododelete, todoread, todoupdate
from buddy.runtime.tools.web_search import fetch_web_page, web_search
from dotenv import load_dotenv
from langfuse import Langfuse
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.toolsets import FunctionToolset, ToolsetTool

load_dotenv()

logger = logging.getLogger(__name__)


def _env_pool_mcp_url() -> str:
    return os.environ.get("BUDDY_ENV_POOL_MCP_URL", "http://127.0.0.1:18001/mcp")


class OptionalMCPServerStreamableHTTP(MCPServerStreamableHTTP):
    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self._available = True

    async def __aenter__(self) -> "OptionalMCPServerStreamableHTTP":
        self._available = True
        try:
            await super().__aenter__()
        except Exception as error:
            self._available = False
            logger.warning("env_pool MCP server unavailable at %s; continuing without MCP tools: %s", self.url, error)
        return self

    async def __aexit__(self, *args: Any) -> bool | None:
        if not self._available:
            return None
        return await super().__aexit__(*args)

    async def get_tools(self, ctx: RunContext[Any]) -> dict[str, ToolsetTool[Any]]:
        if not self._available:
            return {}
        try:
            return await super().get_tools(ctx)
        except Exception as error:
            self._available = False
            logger.warning("Failed to load env_pool MCP tools from %s; continuing without MCP tools: %s", self.url, error)
            return {}


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


def create_agent(
    name: str,
    instructions: str,
    *,
    model: str = "openrouter:openrouter/free",
    enable_web_search: bool = True,
    enable_todo: bool = True,
) -> Agent[None, str]:
    toolsets = [OptionalMCPServerStreamableHTTP(_env_pool_mcp_url())]
    if enable_web_search:
        toolsets.append(web_tools)
    if enable_todo:
        toolsets.append(todo_tools)

    return Agent(
        model=model,
        name=name,
        instructions=instructions,
        retries=5,
        # model="google-gla:gemini-2.5-flash",
        # model="google-gla:gemini-2.5-pro",
        # model="google-gla:gemini-2.5-flash-lite",
        toolsets=cast(Any, toolsets),
        instrument=langfuse_ready,
    )
