import asyncio
from uuid import uuid4

import anyio

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message, new_task
from devtools import pprint
from langfuse import get_client
from pydantic_ai import (
    Agent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    RetryPromptPart,
    ThinkingPart,
    ThinkingPartDelta,
    TextPart,
    TextPartDelta,
    ToolCallPart,
    ToolReturnPart,
)

from buddy.a2a.utils import simple_data_part, simple_text_part
from buddy.session_store import SessionStore


class PyAIAgentExecutor(AgentExecutor):
    def __init__(self, agent: Agent, session_store: SessionStore) -> None:
        self.agent = agent
        self.session_store = session_store

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        print("\n\n\n Recieved new task with query: ", query, "\n")
        message = context.message
        if message is None:
            raise ValueError("Request context missing message")
        context_id = context.context_id
        if context_id is None:
            raise ValueError("Request context missing context_id")
        task = context.current_task or new_task(message)

        updater = TaskUpdater(event_queue, task.id, context_id)

        msg_history = self.session_store.load_messages(context_id)

        self.session_store.append_chat_message(context_id, "user", query)

        await event_queue.enqueue_event(task)
        await updater.update_status(
            TaskState.working, message=new_agent_text_message(f"Recieved new task with query: {query}")
        )
        event_index = self.session_store.next_event_index(context_id)
        self.session_store.append_event(
            context_id,
            event_index,
            {
                "kind": "status-update",
                "contextId": context_id,
                "taskId": task.id,
                "final": False,
                "status": {
                    "state": TaskState.working.value,
                    "message": {
                        "kind": "message",
                        "messageId": str(uuid4()),
                        "role": "agent",
                        "parts": [{"kind": "text", "text": f"Recieved new task with query: {query}"}],
                    },
                },
            },
        )
        event_index += 1

        output = "Agent didn't produce any output"
        res = None
        cur_artifact_id = None
        thinking_artifact_id = None
        tool_calls: dict[str, dict[str, object | None]] = {}
        try:
            langfuse = get_client()
            trace_initialized = False
            send_stream, receive_stream = anyio.create_memory_object_stream()

            async def event_stream_handler(_ctx, events):
                nonlocal trace_initialized
                if not trace_initialized:
                    langfuse.update_current_trace(
                        name="buddy-a2a-request",
                        session_id=context_id,
                        input=query,
                    )
                    trace_initialized = True

                async for event in events:
                    if isinstance(event, PartEndEvent) and isinstance(event.part, TextPart):
                        langfuse.update_current_trace(output=event.part.content)
                    await send_stream.send(event)

            async def run_agent():
                async with send_stream:
                    return await self.agent.run(
                        query,
                        message_history=msg_history,
                        event_stream_handler=event_stream_handler,
                    )

            run_task = asyncio.create_task(run_agent())

            async with receive_stream:
                async for event in receive_stream:
                    pprint(event)

                    if isinstance(event, PartStartEvent):
                        part = event.part
                        cur_artifact_id = str(uuid4())
                        if isinstance(part, TextPart):
                            await updater.add_artifact(
                                [simple_text_part(part.content)],
                                name="output_start",
                                artifact_id=cur_artifact_id,
                            )
                            self.session_store.append_event(
                                context_id,
                                event_index,
                                {
                                    "kind": "artifact-update",
                                    "contextId": context_id,
                                    "taskId": task.id,
                                    "artifact": {
                                        "artifactId": cur_artifact_id,
                                        "name": "output_start",
                                        "parts": [{"kind": "text", "text": part.content}],
                                    },
                                },
                            )
                            event_index += 1
                        if isinstance(part, ThinkingPart):
                            thinking_artifact_id = str(uuid4())
                            await updater.add_artifact(
                                [simple_text_part(part.content)],
                                name="thinking_start",
                                artifact_id=thinking_artifact_id,
                            )
                            self.session_store.append_event(
                                context_id,
                                event_index,
                                {
                                    "kind": "artifact-update",
                                    "contextId": context_id,
                                    "taskId": task.id,
                                    "artifact": {
                                        "artifactId": thinking_artifact_id,
                                        "name": "thinking_start",
                                        "parts": [{"kind": "text", "text": part.content}],
                                    },
                                },
                            )
                            event_index += 1
                    if isinstance(event, PartDeltaEvent):
                        delta = event.delta

                        if isinstance(delta, TextPartDelta):
                            await updater.add_artifact(
                                [simple_text_part(delta.content_delta)],
                                name="output_delta",
                                append=True,
                                artifact_id=cur_artifact_id,
                            )
                            self.session_store.append_event(
                                context_id,
                                event_index,
                                {
                                    "kind": "artifact-update",
                                    "contextId": context_id,
                                    "taskId": task.id,
                                    "append": True,
                                    "artifact": {
                                        "artifactId": cur_artifact_id,
                                        "name": "output_delta",
                                        "parts": [{"kind": "text", "text": delta.content_delta}],
                                    },
                                },
                            )
                            event_index += 1
                        if isinstance(delta, ThinkingPartDelta):
                            content_delta = delta.content_delta if delta.content_delta else ""
                            if thinking_artifact_id is None:
                                thinking_artifact_id = str(uuid4())
                                await updater.add_artifact(
                                    [simple_text_part(content_delta)],
                                    name="thinking_start",
                                    artifact_id=thinking_artifact_id,
                                )
                                self.session_store.append_event(
                                    context_id,
                                    event_index,
                                    {
                                        "kind": "artifact-update",
                                        "contextId": context_id,
                                        "taskId": task.id,
                                        "artifact": {
                                            "artifactId": thinking_artifact_id,
                                            "name": "thinking_start",
                                            "parts": [{"kind": "text", "text": content_delta}],
                                        },
                                    },
                                )
                                event_index += 1
                            else:
                                await updater.add_artifact(
                                    [simple_text_part(content_delta)],
                                    name="thinking_delta",
                                    append=True,
                                    artifact_id=thinking_artifact_id,
                                )
                                self.session_store.append_event(
                                    context_id,
                                    event_index,
                                    {
                                        "kind": "artifact-update",
                                        "contextId": context_id,
                                        "taskId": task.id,
                                        "append": True,
                                        "artifact": {
                                            "artifactId": thinking_artifact_id,
                                            "name": "thinking_delta",
                                            "parts": [{"kind": "text", "text": content_delta}],
                                        },
                                    },
                                )
                                event_index += 1

                    if isinstance(event, PartEndEvent):
                        part = event.part
                        if isinstance(part, TextPart):
                            await updater.add_artifact(
                                [simple_text_part(part.content)],
                                name="output_end",
                                artifact_id=cur_artifact_id,
                            )
                            self.session_store.append_event(
                                context_id,
                                event_index,
                                {
                                    "kind": "artifact-update",
                                    "contextId": context_id,
                                    "taskId": task.id,
                                    "artifact": {
                                        "artifactId": cur_artifact_id,
                                        "name": "output_end",
                                        "parts": [{"kind": "text", "text": part.content}],
                                    },
                                },
                            )
                            event_index += 1
                        if isinstance(part, ThinkingPart):
                            if thinking_artifact_id is None:
                                thinking_artifact_id = str(uuid4())
                            await updater.add_artifact(
                                [simple_text_part(part.content)],
                                name="thinking_end",
                                artifact_id=thinking_artifact_id,
                            )
                            self.session_store.append_event(
                                context_id,
                                event_index,
                                {
                                    "kind": "artifact-update",
                                    "contextId": context_id,
                                    "taskId": task.id,
                                    "artifact": {
                                        "artifactId": thinking_artifact_id,
                                        "name": "thinking_end",
                                        "parts": [{"kind": "text", "text": part.content}],
                                    },
                                },
                            )
                            event_index += 1
                        if isinstance(part, ToolCallPart):
                            tool_call_id = part.tool_call_id
                            tool_calls[tool_call_id] = {
                                "args": part.args,
                            }
                            tool_call_artifact_id = str(uuid4())

                            await updater.add_artifact(
                                [
                                    simple_data_part({
                                        "toolName": part.tool_name,
                                        "toolCallId": tool_call_id,
                                        "args": part.args,
                                    })
                                ],
                                name="tool_call",
                                artifact_id=tool_call_artifact_id,
                            )
                            self.session_store.append_event(
                                context_id,
                                event_index,
                                {
                                    "kind": "artifact-update",
                                    "contextId": context_id,
                                    "taskId": task.id,
                                    "artifact": {
                                        "artifactId": tool_call_artifact_id,
                                        "name": "tool_call",
                                        "parts": [
                                            {
                                                "kind": "data",
                                                "data": {
                                                    "toolName": part.tool_name,
                                                    "toolCallId": tool_call_id,
                                                    "args": part.args,
                                                },
                                            }
                                        ],
                                    },
                                },
                            )
                            event_index += 1

                            await updater.update_status(
                                TaskState.working,
                                message=new_agent_text_message(
                                    f"Calling tool: {part.tool_name} with args: {part.args}"
                                ),
                            )
                            self.session_store.append_event(
                                context_id,
                                event_index,
                                {
                                    "kind": "status-update",
                                    "contextId": context_id,
                                    "taskId": task.id,
                                    "final": False,
                                    "status": {
                                        "state": TaskState.working.value,
                                        "message": {
                                            "kind": "message",
                                            "messageId": str(uuid4()),
                                            "role": "agent",
                                            "parts": [
                                                {
                                                    "kind": "text",
                                                    "text": f"Calling tool: {part.tool_name} with args: {part.args}",
                                                }
                                            ],
                                        },
                                    },
                                },
                            )
                            event_index += 1

                    if isinstance(event, FunctionToolResultEvent):
                        res = event.result

                        if isinstance(res, ToolReturnPart):
                            tool_name = res.tool_name
                            tool_call_id = res.tool_call_id
                            result_content: object = res.content
                            ok = True
                        elif isinstance(res, RetryPromptPart):
                            tool_name = res.tool_name if res.tool_name else "unknown_tool"
                            tool_call_id = res.tool_call_id
                            result_content = res.content
                            ok = False
                        else:
                            tool_name = "unknown_tool"
                            tool_call_id = "unknown_tool_call"
                            result_content = "unknown_result"
                            ok = False

                        tool_call = tool_calls.get(tool_call_id)
                        tool_args = tool_call["args"] if tool_call and "args" in tool_call else None
                        tool_result_artifact_id = str(uuid4())

                        tool_result_data = {
                            "toolName": tool_name,
                            "toolCallId": tool_call_id,
                            "args": tool_args,
                            "result": result_content,
                            "ok": ok,
                        }

                        await updater.add_artifact(
                            [simple_data_part(tool_result_data)],
                            name="tool_result",
                            artifact_id=tool_result_artifact_id,
                        )
                        self.session_store.append_event(
                            context_id,
                            event_index,
                            {
                                "kind": "artifact-update",
                                "contextId": context_id,
                                "taskId": task.id,
                                "artifact": {
                                    "artifactId": tool_result_artifact_id,
                                    "name": "tool_result",
                                    "parts": [
                                        {
                                            "kind": "data",
                                            "data": tool_result_data,
                                        }
                                    ],
                                },
                            },
                        )
                        event_index += 1
                        await updater.update_status(
                            TaskState.working, message=new_agent_text_message("Agent thinking ...")
                        )
                        self.session_store.append_event(
                            context_id,
                            event_index,
                            {
                                "kind": "status-update",
                                "contextId": context_id,
                                "taskId": task.id,
                                "final": False,
                                "status": {
                                    "state": TaskState.working.value,
                                    "message": {
                                        "kind": "message",
                                        "messageId": str(uuid4()),
                                        "role": "agent",
                                        "parts": [{"kind": "text", "text": "Agent thinking ..."}],
                                    },
                                },
                            },
                        )
                        event_index += 1

            res = await run_task
        except Exception as error:
            error_text = str(error)
            error_artifact_id = str(uuid4())
            error_data = {
                "toolName": "agent",
                "toolCallId": "execution_error",
                "args": {"query": query},
                "result": error_text,
                "ok": False,
            }
            await updater.add_artifact(
                [simple_data_part(error_data)],
                name="tool_result",
                artifact_id=error_artifact_id,
            )
            self.session_store.append_event(
                context_id,
                event_index,
                {
                    "kind": "artifact-update",
                    "contextId": context_id,
                    "taskId": task.id,
                    "artifact": {
                        "artifactId": error_artifact_id,
                        "name": "tool_result",
                        "parts": [{"kind": "data", "data": error_data}],
                    },
                },
            )
            event_index += 1

            await updater.failed(new_agent_text_message(error_text))
            self.session_store.append_event(
                context_id,
                event_index,
                {
                    "kind": "status-update",
                    "contextId": context_id,
                    "taskId": task.id,
                    "final": True,
                    "status": {
                        "state": TaskState.failed.value,
                        "message": {
                            "kind": "message",
                            "messageId": str(uuid4()),
                            "role": "agent",
                            "parts": [{"kind": "text", "text": error_text}],
                        },
                    },
                },
            )
            return

        if res is None:
            raise ValueError("Agent produced no result")

        res_output = getattr(res, "output", None)
        if res_output is not None:
            output = res_output

        all_messages = getattr(res, "all_messages", None)
        msgs = all_messages() if callable(all_messages) else []
        msgs_list = list(msgs) if isinstance(msgs, list) else []

        self.session_store.save_messages(context_id, msgs_list)

        self.session_store.append_event(
            context_id,
            event_index,
            {
                "kind": "artifact-update",
                "contextId": context_id,
                "taskId": task.id,
                "artifact": {
                    "artifactId": str(uuid4()),
                    "name": "full_output",
                    "parts": [{"kind": "text", "text": output}],
                },
            },
        )
        event_index += 1

        await updater.add_artifact(
            [simple_text_part(output)],
            name="full_output",
        )

        self.session_store.append_chat_message(context_id, "assistant", output)

        await updater.update_status(TaskState.completed)
        self.session_store.append_event(
            context_id,
            event_index,
            {
                "kind": "status-update",
                "contextId": context_id,
                "taskId": task.id,
                "final": True,
                "status": {
                    "state": TaskState.completed.value,
                },
            },
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancellation is not supported yet")
