from litellm import CustomStreamWrapper
from litellm.types.utils import ModelResponse
from rich.console import Console
from rich.markdown import Markdown


def present(resp: ModelResponse | CustomStreamWrapper, console: Console) -> None:
    if type(resp) is ModelResponse:
        console.print(Markdown(resp["choices"][0]["message"]["content"]))
    elif type(resp) is CustomStreamWrapper:
        for chunk in resp:
            if chunk["choices"][0]["finish_reason"] == "stop":
                break
            console.print(Markdown(chunk["choices"][0]["delta"]["content"]), end="")
    else:
        raise ValueError(f"Unknown response type: {type(resp)}")
