from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from buddy.tools.web_search import fetch_web_page, web_search

load_dotenv()

web_tools = FunctionToolset(
    tools=[
        web_search,
        fetch_web_page,
    ],
)

agent = Agent(
    model="google-gla:gemini-2.5-flash",
    toolsets=[web_tools],
)

app = agent.to_ag_ui()
