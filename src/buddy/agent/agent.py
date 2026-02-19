from dotenv import load_dotenv
from langfuse import get_client
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from buddy.tools.todo import todoadd, tododelete, todoread, todoupdate
from buddy.tools.web_search import fetch_web_page, web_search

load_dotenv()

langfuse = get_client()
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

agent = Agent(
    model="openrouter:openrouter/free",
    # model="google-gla:gemini-2.5-flash",
    # model="google-gla:gemini-2.5-pro",
    # model="google-gla:gemini-2.5-flash-lite",
    toolsets=[web_tools, todo_tools],
    instrument=True,
)
