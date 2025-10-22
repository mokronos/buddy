from datetime import datetime

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


def retrieve_personal_information(person: str):
    if person.lower() == "basti":
        return "Basti is a 29 year old man from Germany. He is a data scientist."
    else:
        return f"No information available for {person}."


def get_current_time():
    return datetime.now().strftime("%H:%M:%S")


def random_tool1(arg1: str, arg2: str):
    import time

    time.sleep(3)
    return f"Result of random long running tool call with args: {arg1} | {arg2}" * 20


def random_tool2(arg1: int, arg2: int):
    return f"Result of random tool call {arg1} | {arg2}"


test_tools = FunctionToolset(
    tools=[
        retrieve_personal_information,
        get_current_time,
    ],
)

random_tools = FunctionToolset(
    tools=[
        random_tool1,
        random_tool2,
    ],
)

agent = Agent(
    model="google-gla:gemini-2.5-flash",
    toolsets=[random_tools],
)

app = agent.to_cli_sync(show_tool_calls=True)
