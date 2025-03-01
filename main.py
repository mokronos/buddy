from typing import Annotated, TypedDict
from openai import OpenAI, pydantic_function_tool
import os
from dotenv import load_dotenv
import subprocess
import time

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel

from web_search import WebSearch

load_dotenv()

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o-mini"
# model_name = "DeepSeek-R1"

llm = ChatOpenAI(
    base_url=endpoint,
    api_key=token,
    model=model_name
)

@tool
def get_current_weather(location: str) -> str:
    """ Get the current weather in a given location. """
    return f"The current weather in {location} is sunny."

@tool
def run_shell_command(command: str) -> str:
    """Executes a shell command and returns the output."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    return result.stdout.strip()

tools = [get_current_weather, run_shell_command, WebSearch()]

llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=tools)

class State(BaseModel):
    messages: Annotated[list, add_messages]
    # docs: list = []

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state.messages)]}

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile()

config = {"configurable": {"thread_id": "1"}}

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

stream_graph_updates("Whats the outcome of the 2025 german election?")

# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break

#         stream_graph_updates(user_input)
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break
