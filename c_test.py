# Import relevant functionality
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv

from web_search import WebSearch

load_dotenv()

# Create the agent
memory = MemorySaver()

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o-mini"
# model_name = "DeepSeek-R1"

model = ChatOpenAI(
    base_url=endpoint,
    api_key=token,
    model=model_name
)
search = WebSearch(num_results=1)
tools = [search]
agent_executor = create_react_agent(model, tools, checkpointer=memory)


# Use the agent
config = {"configurable": {"thread_id": "abc123"}}
for step in agent_executor.stream(
    {"messages": [HumanMessage(content="Whats the outcome of the 2025 german election?")]},
    config,
    stream_mode="values",
):
    step["messages"][-1].pretty_print()
