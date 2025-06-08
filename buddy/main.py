from litellm import CustomStreamWrapper, supports_parallel_function_calling, supports_function_calling
from litellm.types.utils import ModelResponse
from rich.console import Console
from rich.markdown import Markdown

from buddy.llm.llm import call_llm
from buddy.cli.present import present
from buddy.tools.tool import Tool


def main() -> None:
    console = Console()
    # msg = "List me some atractions in paris, give a nice heading and a description. Highlight important words in bold. Use Markdown."
    msg = "Multiply 828 * 9. And 26 * 135. Use the multiply tool to do this."

    messages = [{"role": "user", "content": msg}]

    model = "github/gpt-4.1-mini"
    model = "gemini/gemini-2.0-flash"
    model = "gemini/gemini-2.5-flash-preview-04-17"

    assert supports_function_calling(model=model)
    # assert supports_parallel_function_calling(model=model)

    class Multiply(Tool):
        name = "multiply"
        description = "Multiply two numbers"

        def run(self, x: int, y: int) -> int:
            return x * y

    multiply = Multiply("multiply", "Multiply two numbers")
    tools = [multiply.get_input_schema()]

    resp = call_llm(model=model, messages=messages, stream=False, tools=tools)

    present(resp, console, refresh_frequency=20)


if __name__ == "__main__":
    main()
