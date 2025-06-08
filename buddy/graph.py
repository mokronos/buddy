from typing import Annotated

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from buddy.edges import tools_condition
from buddy.nodes import ChatbotNode, ToolNode
from buddy.tools.tool import Tool
from buddy.log import logger

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
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")

graph_builder.add_conditional_edges(
    "chatbot", tools_condition, {"tools": "tools", END: END}
)

graph_builder.add_edge("tools", "chatbot")

graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

# vis(graph)

resp = graph.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Multiply 828 * 9. And 26 * 135. Use the multiply tool to do this.",
            }
        ]
    },
        config={"configurable": {"main_model": model}},
)

print(resp)
