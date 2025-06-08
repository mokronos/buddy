from langgraph.graph import END


def tools_condition(state: dict) -> str:
    assert state["messages"]

    last_msg = state["messages"][-1]

    assert last_msg["role"] == "assistant"

    if last_msg["tool_calls"]:
        return "tools"

    return END
