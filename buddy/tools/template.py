from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

load_dotenv()


class Template(BaseTool):
    name: str = "template"
    description: str = "Creates a tool definition"

    search_engine: str = ""

    def __init__(self, search_engine: str = "duckduckgo") -> None:
        super().__init__()
        self.search_engine = search_engine

    def _run(
        self,
        tool_type: str,
        messages: Annotated[list, InjectedState("messages")],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_template = f"{tool_type} template: {messages[-1]}"

        return Command(
            update={
                "tool_template": tool_template,
                "messages": [
                    ToolMessage(
                        f"Created {tool_template}",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )


if __name__ == "__main__":
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()

    tool = Template("google")

    resp = tool.invoke(
        {
            "tool_type": "testing",
            "messages": [{"role": "user", "content": "What is the capital of France?"}],
            "tool_call_id": "091205305faef",
        }
    )

    console.print(Markdown(resp.update["messages"][-1].content))
