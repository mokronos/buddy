from langchain_core.runnables import RunnableConfig
from buddy.agents.researcher import graph_builder
from buddy.utils import handle_event
from rich.console import Console
from rich.prompt import Prompt
from langgraph.checkpoint.memory import InMemorySaver


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

        for event in graph.stream({"messages": [{"role": "user", "content": input}]}, config, stream_mode="updates"):
            handle_event(event, console)


if __name__ == "__main__":
    main()
