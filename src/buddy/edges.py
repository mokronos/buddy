from langgraph.graph import END
from pydantic import BaseModel


def tools_condition(state: BaseModel) -> str:
    assert state.messages

    last_msg = state.messages[-1]

    assert last_msg["role"] == "assistant"

    if last_msg.get("tool_calls", None):
        return "tools"

    return "human"


def end_condition(state: BaseModel) -> str:
    assert state.messages

    last_msg = state.messages[-1]

    assert last_msg["role"] == "user"

    if last_msg["content"] == "quit":
        return END

    return "chatbot"
