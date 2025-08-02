from dotenv import load_dotenv
from litellm import CustomStreamWrapper, completion
from litellm.types.utils import ModelResponse

load_dotenv()


def call_llm(
    messages: list[dict],
    model: str = "github/gpt-4.1-mini",
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
    response_format: dict | None = None,
    temperature: float = 0.7,
    stream: bool = False,
) -> ModelResponse | CustomStreamWrapper:
    resp = completion(
        messages=messages,
        model=model,
        tools=tools,
        tool_choice=tool_choice,
        response_format=response_format,
        temperature=temperature,
        stream=stream,
    )

    return resp
