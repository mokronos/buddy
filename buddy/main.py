from litellm import CustomStreamWrapper
from litellm.types.utils import ModelResponse
from rich.console import Console
from rich.markdown import Markdown

from buddy.llm.llm import call_llm
from buddy.cli.present import present


def main() -> None:
    console = Console()
    msg = "List me some atractions in paris, give a nice heading and a description. Highlight important words in bold. Use Markdown."

    messages = [{"role": "user", "content": msg}]

    model = "github/gpt-4.1-mini"
    model = "gemini/gemini-2.0-flash"
    model = "gemini/gemini-2.5-flash-preview-04-17"

    resp = call_llm(model=model, messages=messages, stream=True)

    present(resp, console, refresh_frequency=20)


if __name__ == "__main__":
    main()
