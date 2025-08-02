import os
from typing import Annotated

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, SecretStr

from buddy.tools.planner import Planner
from buddy.tools.web_search import WebSearch

load_dotenv()

token = SecretStr(os.environ["GITHUB_TOKEN"])
# token = SecretStr(os.environ["OPENROUTER_API_KEY"])
endpoint = "https://models.inference.ai.azure.com"
# endpoint = "https://openrouter.ai/api/v1"
model_name = "gpt-4o-mini"
# model_name = "DeepSeek-R1"
# model_name = "mistralai/mistral-small-3.1-24b-instruct:free"

llm = ChatOpenAI(base_url=endpoint, api_key=token, model=model_name)

tools = [WebSearch(full_page=True), Planner()]

llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=tools)


class State(BaseModel):
    messages: Annotated[list, add_messages]


def chatbot(state: State) -> dict:
    """Chatbot."""
    return {"messages": [llm_with_tools.invoke(state.messages)]}


graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
