from typing import Annotated

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict

from buddy.edges import end_condition, tools_condition
from buddy.nodes import ChatbotNode, HumanNode, ToolNode
from buddy.tools.tool import Tool
from buddy.utils import save_graph

model = "gemini/gemini-2.5-flash-preview-04-17"


class Multiply(Tool):
    name = "multiply"
    description = "Multiply two numbers"

    def run(self, x: int, y: int) -> str:
        return str(x * y)


multiply = Multiply("multiply", "Multiply two numbers")
tools = [multiply]


class State(TypedDict):
    messages: Annotated[list, lambda left, right: left + right]


graph_builder = StateGraph(State)

chatbot = ChatbotNode(tools)
tool_node = ToolNode(tools)
human = HumanNode()

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("human", human)

graph_builder.add_edge(START, "human")
graph_builder.add_edge("tools", "chatbot")

graph_builder.add_conditional_edges(
    "chatbot", tools_condition, {"tools": "tools", "human": "human"}
)

graph_builder.add_conditional_edges(
    "human", end_condition, {"chatbot": "chatbot", END: END}
)

checkpointer = InMemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)

save_graph(graph)

config = {
    "configurable": {
        "main_model": model,
        "thread_id": "123",
    }
}

resp = graph.invoke(
    {
        "messages": [
            # {
            #     "role": "user",
            #     "content": "Multiply 828 * 9. And 26 * 135. Use the multiply tool to do this.",
            # }
        ]
    },
    config=config,
)

print(resp)

resp2 = graph.invoke(
    Command(resume="Multiply 828 * 9. And 26 * 135. Use the multiply tool to do this."),
    config=config,
)

print(resp2)
