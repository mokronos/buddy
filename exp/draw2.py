from typing import Annotated

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from buddy.utils import save_graph


class State(BaseModel):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


class ChatbotNode:
    def __call__(self, state: dict) -> dict:
        return {"messages": ["chatbot node response"]}


class ToolNode:
    def __call__(self, state: dict) -> dict:
        return {"messages": ["toolnode response"]}


class HumanNode:
    def __call__(self, state: dict) -> dict:
        return {"messages": ["humannode node response"]}


def tools_condition(state: dict) -> str:
    last_msg = state.messages[-1]
    if last_msg.get("tool_calls", None):
        return "tools"

    return "human"


def end_condition(state: dict) -> str:
    last_msg = state.messages[-1]

    if last_msg["content"] == "quit":
        return END

    return "chatbot"


chatbot = ChatbotNode()
tool_node = ToolNode()
human = HumanNode()

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("human", human)

graph_builder.add_edge(START, "human")
graph_builder.add_edge("tools", "chatbot")
# graph_builder.add_edge("chatbot", "human")

graph_builder.add_conditional_edges("chatbot", tools_condition, {"tools": "tools", "human": "human"})

graph_builder.add_conditional_edges("human", end_condition, {"chatbot": "chatbot", END: END})

graph = graph_builder.compile()

# mermaid_str = graph.get_graph().draw_mermaid()


save_graph(graph)
