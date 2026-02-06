from dotenv import load_dotenv
from pydantic_ai import Agent, InstrumentationSettings
from pydantic_ai.toolsets import FunctionToolset

from buddy.tools.todoread import todoread
from buddy.tools.todowrite import todowrite
from buddy.tools.web_search import fetch_web_page, web_search

from phoenix.otel import register

tracer_provider = register(
    project_name="my-llm-app",
    auto_instrument=False,
    set_global_tracer_provider=False,
)


load_dotenv()

web_tools = FunctionToolset(
    tools=[
        web_search,
        fetch_web_page,
    ],
)

todo_tools = FunctionToolset(
    tools=[
        todowrite,
        todoread,
    ],
)

agent = Agent(
    model="google-gla:gemini-2.5-flash",
    toolsets=[web_tools, todo_tools],
    instrument=InstrumentationSettings(tracer_provider=tracer_provider),
)
