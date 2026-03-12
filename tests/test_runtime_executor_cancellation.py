import asyncio
from pathlib import Path
from typing import Any, cast

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, MessageSendParams, Part, Role, Task, TaskState, TaskStatus, TextPart
from buddy.runtime.a2a.executor import PyAIAgentExecutor
from buddy.session_store import SessionStore


class _FakeTraceSpan:
    def update_trace(self, **_kwargs: Any) -> None:
        return

    def end(self) -> None:
        return


class _FakeLangfuseClient:
    def start_span(self, **_kwargs: Any) -> _FakeTraceSpan:
        return _FakeTraceSpan()

    def flush(self) -> None:
        return


class _BlockingAgent:
    async def run(self, *_args: Any, **_kwargs: Any) -> Any:
        await asyncio.sleep(60)
        raise AssertionError("Cancellation should stop the run before it completes")


def _build_message_params(context_id: str, task_id: str, text: str) -> MessageSendParams:
    return MessageSendParams(
        message=Message(
            messageId="message-1",
            contextId=context_id,
            taskId=task_id,
            role=Role.user,
            parts=[Part(root=TextPart(text=text))],
        )
    )


def test_execute_cancellation_preserves_transcript_but_not_model_history(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("buddy.runtime.a2a.executor.get_client", lambda: _FakeLangfuseClient())

    async def run_test() -> None:
        store = SessionStore(tmp_path / "sessions.db")
        executor = PyAIAgentExecutor(cast(Any, _BlockingAgent()), store)
        event_queue = EventQueue()
        context = RequestContext(
            _build_message_params("ctx-cancel", "task-cancel", "hello"),
            task_id="task-cancel",
            context_id="ctx-cancel",
        )

        execute_task = asyncio.create_task(executor.execute(context, event_queue))

        for _ in range(50):
            if "task-cancel" in executor._active_executions:
                break
            await asyncio.sleep(0.01)
        else:
            raise AssertionError("Active execution was not registered")

        await executor.cancel(context, event_queue)
        await execute_task

        chat_messages = store.load_chat_messages("ctx-cancel")
        assert [message["role"] for message in chat_messages] == ["user", "assistant"]
        assert chat_messages[0]["content"] == "hello"
        assert chat_messages[1]["content"] == "Request canceled."

        assert store.load_messages_payload("ctx-cancel") == []

        events = store.load_events("ctx-cancel")
        assert events[-1]["kind"] == "status-update"
        assert events[-1]["status"]["state"] == TaskState.canceled.value

    asyncio.run(run_test())


def test_cancel_without_active_execution_emits_canceled_status(tmp_path: Path) -> None:
    async def run_test() -> None:
        store = SessionStore(tmp_path / "sessions.db")
        executor = PyAIAgentExecutor(cast(Any, _BlockingAgent()), store)
        event_queue = EventQueue()
        task = Task(
            id="task-fallback",
            contextId="ctx-fallback",
            status=TaskStatus(state=TaskState.working),
            history=[],
        )
        context = RequestContext(
            None,
            task_id="task-fallback",
            context_id="ctx-fallback",
            task=task,
        )

        await executor.cancel(context, event_queue)

        chat_messages = store.load_chat_messages("ctx-fallback")
        assert len(chat_messages) == 1
        assert chat_messages[0]["role"] == "assistant"
        assert chat_messages[0]["content"] == "Request canceled."

        events = store.load_events("ctx-fallback")
        assert events[-1]["kind"] == "status-update"
        assert events[-1]["status"]["state"] == TaskState.canceled.value

    asyncio.run(run_test())
