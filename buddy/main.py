from litellm import CustomStreamWrapper
from litellm.types.utils import ModelResponse
from rich.console import Console
from rich.markdown import Markdown

from buddy.llm.llm import call_llm


def main() -> None:
    console = Console()
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]

    resp = call_llm(messages=messages, stream=True)

    if type(resp) is ModelResponse:
        console.print(Markdown(resp["choices"][0]["message"]["content"]))
    elif type(resp) is CustomStreamWrapper:
        for chunk in resp:
            if chunk["choices"][0]["finish_reason"] == "stop":
                break
            console.print(Markdown(chunk["choices"][0]["delta"]["content"]))
    else:
        raise ValueError(f"Unknown response type: {type(resp)}")


if __name__ == "__main__":
    main()
