from litellm import CustomStreamWrapper
from litellm.types.utils import ModelResponse
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text


def present(resp: ModelResponse | CustomStreamWrapper, console: Console) -> None:
    if type(resp) is ModelResponse:
        # Full response - render as Markdown
        content = resp["choices"][0]["message"]["content"]
        console.print(Markdown(content))
    elif type(resp) is CustomStreamWrapper:
        # Streaming response - collect chunks and render incrementally
        content = ""
        for chunk in resp:
            if chunk["choices"][0]["finish_reason"] == "stop":
                break
            content += chunk["choices"][0]["delta"].get("content", "")
            # Render as Text with markdown support
            console.print(Text.from_markup(content), end="", soft_wrap=True)
        console.print()  # Add final newline
    else:
        raise ValueError(f"Unknown response type: {type(resp)}")
