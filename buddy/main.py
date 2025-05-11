from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

from buddy.agents.researcher import graph_builder
from buddy.utils import handle_event, show_context_size


def main() -> None:
    console = Console()

    checkpointer = InMemorySaver()
    graph = graph_builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "123"}}

    while True:
        input = ""
        input = Prompt.ask("> ")
        if input == "exit":
            break

        for (mode, event) in graph.stream(
            {"messages": [{"role": "user", "content": input}]},
            config,
            stream_mode=["updates", "values"],
        ):
            if mode == "values":
                show_context_size(event, console)
                continue
            console.print(Markdown("---"))
            handle_event(event, console)


if __name__ == "__main__":
    main()
