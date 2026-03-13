import asyncio
from typing import Any

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    Artifact,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils.message import get_message_text
from buddy.runtime.tools.communicate import list_available_agents, send_task


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


def _fake_card(url: str = "http://localhost:8000/a2a") -> AgentCard:
    return AgentCard(
        name="test-agent",
        description="test-agent",
        url=url,
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[],
        version="0.0.1",
    )


def test_send_task_returns_latest_message_text(monkeypatch) -> None:
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

    async def fake_get_agent_card(self) -> AgentCard:
        _ = self
        return _fake_card()

    async def fake_connect(agent_card: AgentCard, *, client_config: object) -> _FakeClient:
        captured["url"] = agent_card.url
        captured["config"] = client_config
        return fake_client

    monkeypatch.setattr("buddy.runtime.tools.communicate.A2ACardResolver.get_agent_card", fake_get_agent_card)
    monkeypatch.setattr("buddy.runtime.tools.communicate.ClientFactory.connect", fake_connect)

    result = asyncio.run(send_task("http://localhost:10001/a2a", "hello from tool"))

    assert result == "final response"
    assert captured["url"] == "http://localhost:10001/a2a"
    assert fake_client.closed is True
    assert len(fake_client.sent_messages) == 1
    assert get_message_text(fake_client.sent_messages[0]) == "hello from tool"


def test_send_task_returns_output_artifact_text(monkeypatch) -> None:
    output_update = TaskArtifactUpdateEvent(
        contextId="ctx-artifact",
        taskId="task-artifact",
        artifact=Artifact(
            artifactId="artifact-output",
            name="full_output",
            parts=[Part(root=TextPart(text="the magic word is please"))],
        ),
    )
    fake_client = _FakeClient(events=[(object(), output_update)])

    async def fake_get_agent_card(self) -> AgentCard:
        _ = self
        return _fake_card()

    async def fake_connect(_agent_card: AgentCard, *, client_config: object) -> _FakeClient:
        _ = client_config
        return fake_client

    monkeypatch.setattr("buddy.runtime.tools.communicate.A2ACardResolver.get_agent_card", fake_get_agent_card)
    monkeypatch.setattr("buddy.runtime.tools.communicate.ClientFactory.connect", fake_connect)

    result = asyncio.run(send_task("http://localhost:10001/a2a", "hello"))

    assert result == "the magic word is please"


def test_send_task_returns_actionable_status_error(monkeypatch) -> None:
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

    async def fake_get_agent_card(self) -> AgentCard:
        _ = self
        return _fake_card()

    async def fake_connect(_agent_card: AgentCard, *, client_config: object) -> _FakeClient:
        _ = client_config
        return fake_client

    monkeypatch.setattr("buddy.runtime.tools.communicate.A2ACardResolver.get_agent_card", fake_get_agent_card)
    monkeypatch.setattr("buddy.runtime.tools.communicate.ClientFactory.connect", fake_connect)

    result = asyncio.run(send_task("http://localhost:10001/a2a", "hello"))

    assert result.startswith("Target agent could not complete the task:")


def test_send_task_sanitizes_connection_errors(monkeypatch) -> None:
    async def fake_get_agent_card(self) -> AgentCard:
        _ = self
        raise RuntimeError("socket timeout traceback details")

    monkeypatch.setattr("buddy.runtime.tools.communicate.A2ACardResolver.get_agent_card", fake_get_agent_card)

    result = asyncio.run(send_task("http://localhost:9999/a2a", "hello"))

    assert "Could not reach the target agent URL" in result
    assert "traceback" not in result
    assert "socket timeout" not in result


def test_send_task_validates_inputs() -> None:
    empty_url = asyncio.run(send_task("", "hello"))
    invalid_url = asyncio.run(send_task("localhost:10001/a2a", "hello"))
    empty_task = asyncio.run(send_task("http://localhost:10001/a2a", "   "))

    assert "agent_url is required" in empty_url
    assert "must start with http:// or https://" in invalid_url
    assert "task is required" in empty_task


def test_list_available_agents_returns_name_url_only(monkeypatch) -> None:
    class _FakeResponse:
        def raise_for_status(self) -> None:
            return

        def json(self) -> dict[str, object]:
            return {
                "agents": [
                    {
                        "key": "managed:demo-subagent",
                        "name": "demo-subagent",
                        "url": "http://localhost:10001/a2a/managed/demo-subagent",
                        "internalUrl": "http://172.17.0.3:8000/a2a",
                        "mountPath": "/a2a/managed/demo-subagent",
                        "status": "running",
                    }
                ]
            }

    class _FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            _ = args, kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        async def get(self, _url: str) -> _FakeResponse:
            return _FakeResponse()

    async def fake_reachable(_client: object, agent_url: str) -> bool:
        return agent_url == "http://172.17.0.3:8000/a2a"

    monkeypatch.setattr("buddy.runtime.tools.communicate.AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr("buddy.runtime.tools.communicate._is_reachable_agent_url", fake_reachable)

    result = asyncio.run(list_available_agents())

    assert result == [{"name": "demo-subagent", "url": "http://172.17.0.3:8000/a2a"}]


def test_list_available_agents_falls_back_to_bridge_discovery(monkeypatch) -> None:
    class _FailingAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            _ = args, kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        async def get(self, _url: str):
            raise RuntimeError("cannot reach control plane")

    async def fake_bridge_discovery() -> list[dict[str, str]]:
        return [{"name": "demo-subagent", "url": "http://172.17.0.3:8000/a2a"}]

    monkeypatch.setattr("buddy.runtime.tools.communicate.AsyncClient", _FailingAsyncClient)
    monkeypatch.setattr("buddy.runtime.tools.communicate._discover_agents_on_bridge_network", fake_bridge_discovery)

    result = asyncio.run(list_available_agents())

    assert result == [{"name": "demo-subagent", "url": "http://172.17.0.3:8000/a2a"}]


def test_list_available_agents_returns_empty_when_none_found(monkeypatch) -> None:
    class _FailingAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            _ = args, kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        async def get(self, _url: str):
            raise RuntimeError("cannot reach control plane")

    async def empty_bridge_discovery() -> list[dict[str, str]]:
        return []

    monkeypatch.setattr("buddy.runtime.tools.communicate.AsyncClient", _FailingAsyncClient)
    monkeypatch.setattr("buddy.runtime.tools.communicate._discover_agents_on_bridge_network", empty_bridge_discovery)

    result = asyncio.run(list_available_agents())

    assert result == []
