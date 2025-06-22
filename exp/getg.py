# from langgraph.checkpoint.memory import InMemorySaver
# from langgraph.graph import END, START, StateGraph
# from pydantic import BaseModel
# from langgraph.graph.message import add_messages
# from typing import Annotated


# class State(BaseModel):
#     messages: Annotated[list, add_messages]

# graph_builder = StateGraph(State)

# class ChatbotNode:
#     def __call__(self, state: dict) -> dict:
#         return {"messages": ["chatbot node response"]}

# chatbot = ChatbotNode()

# graph_builder.add_node("chatbot", chatbot)

# graph_builder.add_edge(START, "chatbot")
# graph_builder.add_edge("chatbot", END)

# checkpointer = InMemorySaver()
# graph = graph_builder.compile(checkpointer=checkpointer)

# from buddy.utils import save_graph
# save_graph(graph)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    foo: str
    bar: Annotated[list[str], add]

def node_a(state: State):
    return {"foo": "a", "bar": ["a"]}

def node_b(state: State):
    return {"foo": "b", "bar": ["b"]}


workflow = StateGraph(State)
workflow.add_node(node_a)
workflow.add_node(node_b)
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", "node_b")
workflow.add_edge("node_b", END)

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

g = graph.get_graph()
