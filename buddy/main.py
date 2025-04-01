import uuid
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.theme import Theme
from rich.table import Table
from rich.prompt import Prompt

from langchain_core.runnables import RunnableConfig
from buddy.graph import graph
from buddy.config import Config

# Initialize theme and console
custom_theme = Theme(
    {"info": "dim cyan", "warning": "magenta", "danger": "bold red", "success": "green"}
)

colors = {"ai": "dim cyan", "tool": "yellow", "user": "bold green"}

console = Console(theme=custom_theme)


def handle_command(command: str):
    """Handle special commands."""
    if command in ["quit", "exit", "q"]:
        console.print("[bold magenta]\n👋 Goodbye![/]")
        sys.exit(0)
    return False


def stream_graph_updates(user_input: str):
    """Stream updates from the graph execution."""
    pending_tool_calls = {}

    # Initialize config with defaults and any environment overrides
    app_config = Config().from_runnable_config(
        {
            "configurable": {
                "thread_id": uuid.uuid4().hex  # Unique thread ID for each session
            }
        }
    )

    for event in graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=app_config.to_runnable_config(),
    ):
        for value in event.values():
            message = value["messages"][-1]

            console.print(Markdown(f"# {message.type}"), style=colors[message.type])

            match message.type:
                case "ai":
                    # Track tool calls
                    if getattr(message, "tool_calls", None):
                        console.print(Markdown("**Assistant called tools:**"))
                        for tool_call in message.tool_calls:
                            pending_tool_calls[tool_call["id"]] = tool_call
                            console.print(
                                f":wrench: [bold cyan]{tool_call['name']}[/]",
                                Panel(
                                    Syntax(
                                        str(tool_call["args"]),
                                        "python",
                                        theme="monokai",
                                        line_numbers=False,
                                    ),
                                    title="Arguments",
                                    title_align="left",
                                    border_style="cyan",
                                ),
                            )
                    # Show regular message
                    elif message.content:
                        console.print(Markdown(message.content))

                case "tool":
                    if message.content:
                        console.print(
                            Panel(
                                Syntax(
                                    message.content,
                                    "json",
                                    theme="monokai",
                                    line_numbers=False,
                                ),
                                title="Tool Result",
                                border_style="yellow",
                                title_align="left",
                                subtitle=f"{message.name}",
                            )
                        )


def main() -> None:
    """Entry point for the application."""
    console.print(Markdown("# 🤖 Welcome to **Buddy Chat**!"))
    console.print("""
[bold blue]Available commands:[/]
- [cyan]tools[/]: List all available tools
- [cyan]help <tool>[/]: Show detailed help for a tool
- [cyan]quit[/], [cyan]exit[/], or [cyan]q[/]: Leave the chat
    """)

    while True:
        try:
            console.print(Markdown("# YOU"), style=colors["user"])
            user_input = Prompt.ask("[bold green]>[/]")

            # Handle special commands
            if handle_command(user_input):
                continue

            # Process regular input
            stream_graph_updates(user_input)

        except KeyboardInterrupt:
            print("\n\nSession interrupted. Exiting...")
            break
        except Exception as e:
            console.print(f"[danger]An error occurred: {str(e)}[/]")
            continue


if __name__ == "__main__":
    from prompt_toolkit import prompt
    text = prompt("Enter some text: ")
    print(text)
    # main()
