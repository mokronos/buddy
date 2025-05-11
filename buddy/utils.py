from rich.console import Console
from langchain_core.messages import AIMessage, ToolMessage
import tiktoken

def handle_event(event: dict, console: Console) -> None:
        for node, val in event.items():
            print(f"Node: {node}")

            if isinstance(val, dict):
                val = [val]
            for v in val:
                msg = v.get("messages")[-1]
                if isinstance(msg, ToolMessage):
                    console.print(msg.content)
                elif isinstance(msg, AIMessage):
                    if msg.content:
                        console.print(f"AI: {msg.content}")
                    elif msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            console.print(f"Tool call: {tool_call['name']} | {tool_call['args']}")



def show_context_size(event: dict, console: Console) -> None:

    msgs = event.get("messages")

    encoding = tiktoken.encoding_for_model("gpt-4o")

    total_tokens = 0
    for msg in msgs:
        total_tokens += len(encoding.encode(msg.content))

    console.print(f"Context size: {total_tokens}")
