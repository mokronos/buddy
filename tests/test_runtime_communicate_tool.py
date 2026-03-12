import asyncio
from typing import Any

from a2a.types import Message, Part, Role, TaskState, TaskStatus, TaskStatusUpdateEvent, TextPart
from a2a.utils.message import get_message_text
from buddy.runtime.tools.communicate import communicate


class _FakeClient:
    def __init__(self, events: list[object]) -> None:
        self._events = events
        self.closed = False
        self.sent_messages: list[Message] = []

    async def send_message(self, message: Message):
        self.sent_messages.append(message)
        for event in self._events:
            yield event

    async def close(self) -> None:
        self.closed = True


def test_communicate_returns_latest_message_text(monkeypatch) -> None:
    fake_client = _FakeClient(
        events=[
            Message(
                role=Role.user,
                parts=[Part(root=TextPart(text="first response"))],
                messageId="msg-1",
                contextId="ctx-1",
            ),
            Message(
                role=Role.user,
                parts=[Part(root=TextPart(text="final response"))],
                messageId="msg-2",
                contextId="ctx-1",
            ),
        ]
    )
    captured: dict[str, Any] = {}

    async def fake_connect(url: str, *, client_config: object) -> _FakeClient:
        captured["url"] = url
        captured["config"] = client_config
        return fake_client

    monkeypatch.setattr("buddy.runtime.tools.communicate.ClientFactory.connect", fake_connect)

    result = asyncio.run(communicate("http://localhost:10001/a2a", "hello from tool"))

    assert result == "final response"
    assert captured["url"] == "http://localhost:10001/a2a"
    assert fake_client.closed is True
    assert len(fake_client.sent_messages) == 1
    assert get_message_text(fake_client.sent_messages[0]) == "hello from tool"


def test_communicate_returns_status_failure_message(monkeypatch) -> None:
    failed_update = TaskStatusUpdateEvent(
        contextId="ctx-status",
        taskId="task-status",
        status=TaskStatus(
            state=TaskState.failed,
            message=Message(
                role=Role.user,
                parts=[Part(root=TextPart(text="destination agent rejected the task"))],
                messageId="status-msg",
                contextId="ctx-status",
            ),
        ),
        final=True,
    )
    fake_client = _FakeClient(events=[(object(), failed_update)])

    async def fake_connect(_url: str, *, client_config: object) -> _FakeClient:
        _ = client_config
        return fake_client

    monkeypatch.setattr("buddy.runtime.tools.communicate.ClientFactory.connect", fake_connect)

    result = asyncio.run(communicate("http://localhost:10001/a2a", "hello"))

    assert result == "Agent request failed: destination agent rejected the task"
    assert fake_client.closed is True


def test_communicate_handles_connect_errors(monkeypatch) -> None:
    async def fake_connect(_url: str, *, client_config: object) -> _FakeClient:
        _ = client_config
        raise RuntimeError("connection refused")

    monkeypatch.setattr("buddy.runtime.tools.communicate.ClientFactory.connect", fake_connect)

    result = asyncio.run(communicate("http://localhost:9999/a2a", "hello"))

    assert "Failed to connect to agent" in result
    assert "connection refused" in result
