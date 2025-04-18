from rich.console import Console
from langchain_core.messages import AIMessage, ToolMessage

def handle_event(event: dict, console: Console) -> None:
        for node, val in event.items():
            print(f"Node: {node}")

            msg = val.get("messages")[-1]
            if isinstance(msg, ToolMessage):
                console.print(msg.content)
            elif isinstance(msg, AIMessage):
                if msg.content:
                    console.print(f"AI: {msg.content}")
                elif msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        console.print(f"Tool call: {tool_call['name']} | {tool_call['args']}")
