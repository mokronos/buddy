from dotenv import load_dotenv
from langfuse import get_client
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from buddy.tools.todoadd import todoadd
from buddy.tools.tododelete import tododelete
from buddy.tools.todoread import todoread
from buddy.tools.todoupdate import todoupdate
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
    model="google-gla:gemini-2.5-flash",
    toolsets=[web_tools, todo_tools],
    instrument=True,
)
