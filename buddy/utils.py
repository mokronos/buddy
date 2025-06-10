from langgraph.graph.graph import CompiledGraph
from rich.console import Console
from langchain_core.messages import AIMessage, ToolMessage
import tiktoken

from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

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

def vis(compiled_graph) -> None:
    # draw_mermaid_png() returns bytes
    png_bytes = compiled_graph.get_graph().draw_mermaid_png()

    # Load bytes into a PIL Image
    img = Image.open(BytesIO(png_bytes))

    # Optional: convert to format matplotlib likes (e.g., RGB)
    img = img.convert('RGB')

    # Show with matplotlib
    plt.imshow(img)
    plt.axis('off')  # optional
    plt.show()

def save_graph(compiled_graph: CompiledGraph) -> None:
    mermaid_str = compiled_graph.get_graph().draw_mermaid()

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
      <script>
        mermaid.initialize({{ startOnLoad: true }});
      </script>
    </head>
    <body>
      <div class="mermaid">
        {mermaid_str}
      </div>
    </body>
    </html>
    """

    with open("diagram.html", "w") as f:
        f.write(html_template)
