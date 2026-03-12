import asyncio
from dataclasses import dataclass
from typing import Any, cast
from uuid import uuid4

import anyio
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message, new_task
from buddy.runtime.a2a.event_writer import SessionEventWriter
from buddy.runtime.a2a.utils import simple_data_part, simple_text_part
from buddy.session_store import SessionStore
from devtools import pprint
from langfuse import get_client
from pydantic_ai import (
    Agent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    RetryPromptPart,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
    ToolReturnPart,
)


@dataclass
class ActiveExecution:
    run_task: asyncio.Task[Any] | None
    context_id: str
    updater: TaskUpdater
    writer: SessionEventWriter
    cancellation_requested: bool = False
    cancellation_status_emitted: bool = False
    cancellation_transcript_written: bool = False


class PyAIAgentExecutor(AgentExecutor):
    def __init__(
        self,
        agent: Agent,
        session_store: SessionStore,
    ) -> None:
        self.agent = agent
        self.session_store = session_store
        self._active_executions: dict[str, ActiveExecution] = {}

    async def _emit_cancellation_status(self, execution: ActiveExecution) -> None:
        if execution.cancellation_status_emitted:
            return

        cancel_message = "Request canceled by user."
        try:
            await execution.updater.cancel(new_agent_text_message(cancel_message))
        except RuntimeError:
            pass
        execution.writer.append_status_update(TaskState.canceled, cancel_message, final=True)
        execution.cancellation_status_emitted = True

    def _append_cancellation_transcript(self, execution: ActiveExecution) -> None:
        if execution.cancellation_transcript_written:
            return

        self.session_store.append_chat_message(execution.context_id, "assistant", "Request canceled.")
        execution.cancellation_transcript_written = True

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        message = context.message
        if message is None:
            raise ValueError("Request context missing message")
        context_id = context.context_id
        if context_id is None:
            raise ValueError("Request context missing context_id")
        task = context.current_task or new_task(message)

        updater = TaskUpdater(event_queue, task.id, context_id)
        writer = SessionEventWriter(session_store=self.session_store, context_id=context_id, task_id=task.id)
        execution = ActiveExecution(
            run_task=None,
            context_id=context_id,
            updater=updater,
            writer=writer,
        )
        self._active_executions[task.id] = execution

        msg_history = self.session_store.load_messages(context_id)

        self.session_store.append_chat_message(context_id, "user", query)

        await event_queue.enqueue_event(task)
        await updater.update_status(
            TaskState.working, message=new_agent_text_message(f"Recieved new task with query: {query}")
        )
        writer.append_status_update(TaskState.working, f"Recieved new task with query: {query}")

        output = "Agent didn't produce any output"
        res = None
        cur_artifact_id = None
        thinking_artifact_id = None
        tool_calls: dict[str, dict[str, object | None]] = {}
        langfuse = None
        trace_span = None
        try:
            langfuse = get_client()
            trace_span = langfuse.start_span(name="buddy-a2a-request")
            trace_span.update_trace(
                name="buddy-a2a-request",
                session_id=context_id,
                input=query,
            )
            send_stream, receive_stream = anyio.create_memory_object_stream()

            async def event_stream_handler(_ctx, events):
                async for event in events:
                    if isinstance(event, PartEndEvent) and isinstance(event.part, TextPart):
                        trace_span.update_trace(output=event.part.content)
                    await send_stream.send(event)

            async def run_agent():
                async with send_stream:
                    agent_with_deps = cast(Any, self.agent)
                    return await agent_with_deps.run(
                        query,
                        message_history=msg_history,
                        event_stream_handler=event_stream_handler,
                    )

            run_task = asyncio.create_task(run_agent())
            execution.run_task = run_task

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
                            writer.append_artifact_text(
                                artifact_id=cur_artifact_id,
                                name="output_start",
                                text=part.content,
                            )
                        if isinstance(part, ThinkingPart):
                            thinking_artifact_id = str(uuid4())
                            await updater.add_artifact(
                                [simple_text_part(part.content)],
                                name="thinking_start",
                                artifact_id=thinking_artifact_id,
                            )
                            writer.append_artifact_text(
                                artifact_id=thinking_artifact_id,
                                name="thinking_start",
                                text=part.content,
                            )
                    if isinstance(event, PartDeltaEvent):
                        delta = event.delta

                        if isinstance(delta, TextPartDelta):
                            await updater.add_artifact(
                                [simple_text_part(delta.content_delta)],
                                name="output_delta",
                                append=True,
                                artifact_id=cur_artifact_id,
                            )
                            writer.append_artifact_text(
                                artifact_id=cur_artifact_id,
                                name="output_delta",
                                text=delta.content_delta,
                                append=True,
                            )
                        if isinstance(delta, ThinkingPartDelta):
                            content_delta = delta.content_delta if delta.content_delta else ""
                            if thinking_artifact_id is None:
                                thinking_artifact_id = str(uuid4())
                                await updater.add_artifact(
                                    [simple_text_part(content_delta)],
                                    name="thinking_start",
                                    artifact_id=thinking_artifact_id,
                                )
                                writer.append_artifact_text(
                                    artifact_id=thinking_artifact_id,
                                    name="thinking_start",
                                    text=content_delta,
                                )
                            else:
                                await updater.add_artifact(
                                    [simple_text_part(content_delta)],
                                    name="thinking_delta",
                                    append=True,
                                    artifact_id=thinking_artifact_id,
                                )
                                writer.append_artifact_text(
                                    artifact_id=thinking_artifact_id,
                                    name="thinking_delta",
                                    text=content_delta,
                                    append=True,
                                )

                    if isinstance(event, PartEndEvent):
                        part = event.part
                        if isinstance(part, TextPart):
                            await updater.add_artifact(
                                [simple_text_part(part.content)],
                                name="output_end",
                                artifact_id=cur_artifact_id,
                            )
                            writer.append_artifact_text(
                                artifact_id=cur_artifact_id,
                                name="output_end",
                                text=part.content,
                            )
                        if isinstance(part, ThinkingPart):
                            if thinking_artifact_id is None:
                                thinking_artifact_id = str(uuid4())
                            await updater.add_artifact(
                                [simple_text_part(part.content)],
                                name="thinking_end",
                                artifact_id=thinking_artifact_id,
                            )
                            writer.append_artifact_text(
                                artifact_id=thinking_artifact_id,
                                name="thinking_end",
                                text=part.content,
                            )
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
                            writer.append_artifact_data(
                                artifact_id=tool_call_artifact_id,
                                name="tool_call",
                                data={
                                    "toolName": part.tool_name,
                                    "toolCallId": tool_call_id,
                                    "args": part.args,
                                },
                            )

                            await updater.update_status(
                                TaskState.working,
                                message=new_agent_text_message(
                                    f"Calling tool: {part.tool_name} with args: {part.args}"
                                ),
                            )
                            writer.append_status_update(
                                TaskState.working,
                                f"Calling tool: {part.tool_name} with args: {part.args}",
                            )

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
                        writer.append_artifact_data(
                            artifact_id=tool_result_artifact_id,
                            name="tool_result",
                            data=cast(dict[str, object], tool_result_data),
                        )
                        await updater.update_status(
                            TaskState.working, message=new_agent_text_message("Agent thinking ...")
                        )
                        writer.append_status_update(TaskState.working, "Agent thinking ...")

            res = await run_task
        except asyncio.CancelledError:
            if execution.cancellation_requested:
                self._append_cancellation_transcript(execution)
                if trace_span is not None:
                    trace_span.end()
                if langfuse is not None:
                    langfuse.flush()
                return
            raise
        except Exception as error:
            error_text = str(error)
            await updater.failed(new_agent_text_message(error_text))
            writer.append_status_update(TaskState.failed, error_text, final=True)
            raise RuntimeError(error_text) from error
        finally:
            self._active_executions.pop(task.id, None)

        if res is None:
            raise ValueError("Agent produced no result")

        res_output = getattr(res, "output", None)
        if res_output is not None:
            output = res_output

        all_messages = getattr(res, "all_messages", None)
        msgs = all_messages() if callable(all_messages) else []
        msgs_list = list(msgs) if isinstance(msgs, list) else []

        self.session_store.save_messages(context_id, msgs_list)

        writer.append_artifact_text(artifact_id=str(uuid4()), name="full_output", text=output)

        await updater.add_artifact(
            [simple_text_part(output)],
            name="full_output",
        )

        self.session_store.append_chat_message(context_id, "assistant", output)
        trace_span.end()
        langfuse.flush()

        await updater.update_status(TaskState.completed)
        writer.append_status_update(TaskState.completed, final=True)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        if task_id is None:
            raise ValueError("Request context missing task_id")
        context_id = context.context_id
        if context_id is None:
            raise ValueError("Request context missing context_id")

        execution = self._active_executions.get(task_id)
        if execution is None:
            task = context.current_task
            if task is None or task.status.state in {
                TaskState.completed,
                TaskState.canceled,
                TaskState.failed,
                TaskState.rejected,
            }:
                raise RuntimeError("Task is not actively running")

            fallback_execution = ActiveExecution(
                run_task=None,
                context_id=context_id,
                updater=TaskUpdater(event_queue, task_id, context_id),
                writer=SessionEventWriter(
                    session_store=self.session_store,
                    context_id=context_id,
                    task_id=task_id,
                ),
                cancellation_requested=True,
            )
            await self._emit_cancellation_status(fallback_execution)
            self._append_cancellation_transcript(fallback_execution)
            return

        execution.cancellation_requested = True
        if execution.run_task is not None:
            execution.run_task.cancel()
        await self._emit_cancellation_status(execution)
