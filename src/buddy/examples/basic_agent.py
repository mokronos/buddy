import asyncio
from collections.abc import AsyncIterable
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, ToolResult
from pydantic_ai.messages import (
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    HandleResponseEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.toolsets import FunctionToolset

load_dotenv()


class AgentContext(BaseModel):
    current_task: str


agent = Agent(
    model="google-gla:gemini-2.5-flash",
    deps_type=AgentContext,
    system_prompt=("You are a helpful assistant."),
)


async def process_tool_call(
    ctx: RunContext[AgentContext],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    return await call_tool(name, tool_args, {"deps": ctx.deps})


def task_tracker(ctx: RunContext[AgentContext], task: str) -> str:
    """A tool that tracks the current task."""
    ctx.deps.current_task = task

    return "Task successfully updated. Current task is now: " + task


basic_tools = FunctionToolset(
    tools=[
        task_tracker,
    ]
)


async def event_stream_handler(
    ctx: RunContext[AgentContext],
    event_stream: AsyncIterable[AgentStreamEvent | HandleResponseEvent],
):
    async for event in event_stream:
        if isinstance(event, PartStartEvent):
            print(f"[Request] Starting part {event.index}: {event.part!r}")
        elif isinstance(event, PartDeltaEvent):
            if isinstance(event.delta, TextPartDelta):
                print(f"[Request] Part {event.index} text delta: {event.delta.content_delta!r}")
            elif isinstance(event.delta, ThinkingPartDelta):
                print(f"[Request] Part {event.index} thinking delta: {event.delta.content_delta!r}")
            elif isinstance(event.delta, ToolCallPartDelta):
                print(f"[Request] Part {event.index} args delta: {event.delta.args_delta}")
        elif isinstance(event, FunctionToolCallEvent):
            print(
                f"[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})"
            )
        elif isinstance(event, FunctionToolResultEvent):
            print(f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}")
        elif isinstance(event, FinalResultEvent):
            print(f"[Result] The model starting producing a final result (tool_name={event.tool_name})")


async def main() -> None:
    # prompt = "Which of these tasks is the most important? A. Clean my house B. Play a video game. C. Eat (im really hungry). After you decided, put the task as the current task with the task tracker tool."
    # prompt = "What tools do you have available?"
    prompt = "Please set 'Cleaning house' as the current task."
    print(f"Prompt: {prompt}")

    deps = AgentContext(current_task="")

    async with agent.run_stream(
        prompt, toolsets=[basic_tools], event_stream_handler=event_stream_handler, deps=deps
    ) as agent_run:
        async for output in agent_run.stream_text():
            print(f"[Output] {output}")


if __name__ == "__main__":
    asyncio.run(main())
