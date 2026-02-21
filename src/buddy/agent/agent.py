from dotenv import load_dotenv
from langfuse import Langfuse
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from buddy.tools.todo import todoadd, tododelete, todoread, todoupdate
from buddy.tools.web_search import fetch_web_page, web_search

load_dotenv()

langfuse = Langfuse(blocked_instrumentation_scopes=["a2a-python-sdk"])
# Verify connection
try:
    if langfuse.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")
except Exception as e:
    print(f"Langfuse connection error (skipping): {e}")

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


def create_agent(name: str) -> Agent:
    return Agent(
        model="openrouter:openrouter/free",
        name=name,
        retries=5,
        # model="google-gla:gemini-2.5-flash",
        # model="google-gla:gemini-2.5-pro",
        # model="google-gla:gemini-2.5-flash-lite",
        toolsets=[web_tools, todo_tools],
        instrument=True,
    )


agent = create_agent("buddy-agent")
second_agent = create_agent("buddy-agent-2")

agents = {
    "buddy": agent,
    "buddy-2": second_agent,
}
