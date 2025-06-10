from langgraph.graph import END


def tools_condition(state: dict) -> str:
    assert state.messages

    last_msg = state.messages[-1]

    assert last_msg["role"] == "assistant"

    if last_msg.get("tool_calls", None):
        return "tools"

    return "human"

def end_condition(state: dict) -> str:
    assert state.messages

    last_msg = state.messages[-1]

    assert last_msg["role"] == "user"

    if last_msg["content"] == "quit":
        return END

    return "chatbot"
