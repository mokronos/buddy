from __future__ import annotations

from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message, new_task
from devtools import pprint
from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallPart,
)

from buddy.a2a.utils import simple_text_part
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
        async for event in self.agent.run_stream_events(query, message_history=msg_history):
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
                if isinstance(part, ToolCallPart):
                    await updater.update_status(
                        TaskState.working,
                        message=new_agent_text_message(f"Calling tool: {part.tool_name} with args: {part.args}"),
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

                text = f"Tool {res.tool_name} returned: {res.content}"

                await updater.add_artifact(
                    [simple_text_part(text)],
                    name="tool_result",
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
                            "name": "tool_result",
                            "parts": [{"kind": "text", "text": text}],
                        },
                    },
                )
                event_index += 1
                await updater.update_status(TaskState.working, message=new_agent_text_message("Agent thinking ..."))
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

            if isinstance(event, AgentRunResultEvent):
                res = event.result

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
