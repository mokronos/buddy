import json
from litellm import CustomStreamWrapper
from litellm.types.utils import ModelResponse


def get_resp(
    resp: ModelResponse | CustomStreamWrapper,
) -> None:
    if type(resp) is ModelResponse:
        response_msg = resp.choices[0].message
        return response_msg
        tool_calls = response_msg.tool_calls

        if tool_calls:
            console.print("Tool Calls:")
            for tool_call in tool_calls:
                print(tool_call)

        # Full response - render as Markdown
        content = resp["choices"][0]["message"]["content"]
        return content
    elif type(resp) is CustomStreamWrapper:
        raise NotImplementedError("Streaming response not supported yet")
    else:
        raise ValueError(f"Unknown response type: {type(resp)}")


def run_tool(tools, tool_call):
    tool_name = tool_call["function"]["name"]
    tool = tools[tool_name]
    tool_args = json.loads(tool_call["function"]["arguments"])

    msg = {
        "tool_call_id": tool_call["id"],
        "role": "tool",
        "name": tool_name,
        "content": tool(**tool_args),
    }

    return msg

def get_tool_call_msg(tool_call) -> dict:

    tool_calls = []
    for tool_call in tool_call.tool_calls:
        tool_calls.append({
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            }
        })

    return {
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
    }
