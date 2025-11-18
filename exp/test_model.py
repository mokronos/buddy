import asyncio
import json
from time import sleep

from pydantic_ai import Agent, ModelResponse, ToolCallPart
from pydantic_ai.models.function import DeltaToolCall, DeltaToolCalls, FunctionModel
from pydantic_ai.models.test import TestModel

model = TestModel()


def call_model(messages, info):
    # return ModelResponse(parts=[TextPart("Hello, I'm a test model!")])
    return ModelResponse(parts=[ToolCallPart("get_time"), ToolCallPart("get_date")])


async def call_model_stream(messages, info):
    if len(messages) == 1:
        tool_calls = {
            1: DeltaToolCall(
                name="long_running_tool_call",
                tool_call_id="1",
                json_args=json.dumps({
                    "arg1": "arg1",
                    "arg2": "arg2",
                }),
            ),
            2: DeltaToolCall(
                name="quick_tool_call",
                tool_call_id="2",
                json_args=json.dumps({
                    "arg1": 1,
                    "arg2": 2,
                }),
            ),
        }
        await asyncio.sleep(1)

        yield DeltaToolCalls(tool_calls)

    else:
        await asyncio.sleep(1)
        yield "Finished"


function_model = FunctionModel(call_model, stream_function=call_model_stream)


def long_running_tool_call(arg1: str, arg2: str):
    sleep(3)
    return f"Result of long running tool call with args: {arg1} | {arg2}" * 20


def quick_tool_call(arg1: int, arg2: int):
    sleep(0.5)
    return f"Result of quick tool call {arg1} | {arg2}"


agent = Agent(model=function_model, tools=[long_running_tool_call, quick_tool_call])


agent.to_cli_sync(show_tool_calls=True)
