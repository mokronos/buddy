from langchain_core.runnables import RunnableConfig
from buddy.llm.llm import call_llm
from buddy.llm.utils import get_resp, get_tool_call_msg, run_tool
from buddy.log import logger

class ChatbotNode:
    def __init__(self, tools: list) -> None:
        self.tools = tools
        self.tool_schemas = [t.get_input_schema() for t in self.tools]

    def __call__(self, state: dict, config: RunnableConfig) -> dict:
        logger.debug(f"Calling {config['configurable'].get('main_model')} with messages: {state['messages']}")
        resp = call_llm(model=config.get("main_model", "gemini/gemini-2.5-flash-preview-04-17"), messages=state["messages"], stream=False, tools=self.tool_schemas)

        resp = get_resp(resp)

        if resp.tool_calls:
            resp = get_tool_call_msg(resp)

        return {"messages": [resp]}


class ToolNode:
    def __init__(self, tools: list) -> None:

        self.tools = tools
        self.tool_map = {t.name: t for t in self.tools}
        self.tool_schemas = [t.get_input_schema() for t in self.tools]

    def __call__(self, state: dict) -> dict:

        assert state["messages"]
        last_msg = state["messages"][-1]

        tool_responses = []

        for tool_call in last_msg["tool_calls"]:
            tool_resp = run_tool(self.tool_map, tool_call)
            tool_responses.append(tool_resp)

        return {"messages": tool_responses}
