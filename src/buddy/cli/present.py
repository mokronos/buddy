from litellm import CustomStreamWrapper
from litellm.types.utils import ModelResponse
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown


def present(
    resp: ModelResponse | CustomStreamWrapper,
    console: Console,
    refresh_frequency: int = 10,
) -> None:
    if type(resp) is ModelResponse:

        response_msg = resp.choices[0].message
        tool_calls = response_msg.tool_calls

        if tool_calls:
            console.print("Tool Calls:")
            for tool_call in tool_calls:
                print(tool_call)

        # Full response - render as Markdown
        content = resp["choices"][0]["message"]["content"]
        console.print(Markdown(content))
    elif type(resp) is CustomStreamWrapper:
        # Streaming response - collect chunks and render incrementally
        content = ""
        with Live(
            Markdown(""), console=console, refresh_per_second=refresh_frequency
        ) as live:
            for chunk in resp:
                if chunk["choices"][0]["finish_reason"] == "stop":
                    break
                content += chunk["choices"][0]["delta"].get("content", "")
                live.update(Markdown(content))
    else:
        raise ValueError(f"Unknown response type: {type(resp)}")
