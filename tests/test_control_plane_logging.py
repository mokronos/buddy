import json
import logging
from pathlib import Path
from threading import Lock
from typing import ClassVar

from buddy.control_plane.external_agents import ExternalAgentManager
from buddy.control_plane.managed_agents import ManagedAgentManager, ManagedAgentRecord
from buddy.shared.logging import configure_logging
from fastapi.testclient import TestClient

from buddy.control_plane import routes_proxy
from buddy.control_plane import server as server_module


class _CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.events: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return
        if isinstance(payload, dict):
            self.events.append(payload)


def test_request_logging_emits_single_wide_event(monkeypatch) -> None:
    class _FakeManagedAgentManager:
        def reconcile_from_docker(self) -> list[object]:
            return []

        def list_agents(self) -> list[object]:
            return []

    class _FakeExternalAgentManager:
        def list_agents(self) -> list[object]:
            return []

        def get_agent(self, agent_id: str) -> None:
            return None

    monkeypatch.setattr(server_module, "ManagedAgentManager", _FakeManagedAgentManager)
    monkeypatch.setattr(server_module, "ExternalAgentManager", _FakeExternalAgentManager)

    handler = _CaptureHandler()
    logger = logging.getLogger("buddy")
    logger.addHandler(handler)
    configure_logging("buddy-control-plane-test")

    try:
        with TestClient(server_module.create_app()) as client:
            response = client.get("/agents", headers={"X-Request-ID": "req-123"})
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"

    request_events = [event for event in handler.events if event.get("event") == "http_request_completed"]
    assert len(request_events) == 1
    assert request_events[0]["request_id"] == "req-123"
    assert request_events[0]["method"] == "GET"
    assert request_events[0]["path"] == "/agents"
    assert request_events[0]["status_code"] == 200
    assert request_events[0]["outcome"] == "success"
    assert request_events[0]["service"] == "buddy-control-plane"


def test_proxy_propagates_request_id_upstream(monkeypatch) -> None:
    captured_headers: list[dict[str, str]] = []

    class _FakeManagedAgentManager:
        def reconcile_from_docker(self) -> list[object]:
            return []

        def list_agents(self) -> list[object]:
            return []

        def get_agent(self, agent_id: str):
            return type(
                "_ManagedRecord",
                (),
                {"agent_id": agent_id, "status": "running", "a2a_mount_path": "/a2a"},
            )()

        def resolve_target(self, agent_id: str, path: str) -> str:
            return f"http://upstream.test{path}"

    class _FakeExternalAgentManager:
        def list_agents(self) -> list[object]:
            return []

        def get_agent(self, agent_id: str) -> None:
            return None

    class _FakeResponse:
        status_code: ClassVar[int] = 200
        headers: ClassVar[dict[str, str]] = {"content-type": "application/json"}

        async def aread(self) -> bytes:
            return b'{"ok": true}'

        async def aclose(self) -> None:
            return None

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            return None

        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        def build_request(self, method: str, url: str, **kwargs):
            headers = kwargs.get("headers", {})
            captured_headers.append(dict(headers))
            return object()

        async def send(self, request, stream: bool = False) -> _FakeResponse:
            return _FakeResponse()

        async def aclose(self) -> None:
            return None

        async def get(self, url: str, headers: dict[str, str] | None = None) -> _FakeResponse:
            captured_headers.append(dict(headers or {}))
            return _FakeResponse()

    monkeypatch.setattr(server_module, "ManagedAgentManager", _FakeManagedAgentManager)
    monkeypatch.setattr(server_module, "ExternalAgentManager", _FakeExternalAgentManager)
    monkeypatch.setattr(routes_proxy.httpx, "AsyncClient", _FakeAsyncClient)

    with TestClient(server_module.create_app()) as client:
        response = client.post(
            "/a2a/managed/demo",
            headers={"X-Request-ID": "req-456", "content-type": "application/json"},
            content=b"{}",
        )

    assert response.status_code == 200
    assert captured_headers[-1]["x-request-id"] == "req-456"


def test_external_agent_create_logs_structured_event(tmp_path) -> None:
    handler = _CaptureHandler()
    logger = logging.getLogger("buddy")
    logger.addHandler(handler)
    configure_logging("buddy-control-plane-test")

    try:
        manager = ExternalAgentManager(registry_path=tmp_path / "external_agents.json")
        manager.create_agent(agent_id="demo", base_url="http://example.com")
    finally:
        logger.removeHandler(handler)

    create_events = [event for event in handler.events if event.get("event") == "external_agent_create_completed"]
    assert len(create_events) == 1
    assert create_events[0]["agent_id"] == "demo"
    assert create_events[0]["base_url"] == "http://example.com"
    assert create_events[0]["outcome"] == "success"


def test_managed_agent_update_config_logs_redacted_event(tmp_path) -> None:
    agent_id = "demo-agent"
    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
""",
        encoding="utf-8",
    )

    manager = object.__new__(ManagedAgentManager)
    manager._lock = Lock()
    manager._records = {
        agent_id: ManagedAgentRecord(
            agent_id=agent_id,
            image="buddy-agent-runtime:latest",
            config_path=str(config_path),
            config_mount_path="/etc/buddy/agent.yaml",
            container_port=8000,
            a2a_mount_path="/a2a",
            container_id="abc123",
            host_port=11001,
            status="running",
            last_error=None,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
    }
    manager._registry_path = Path(tmp_path / "registry.json")
    manager._now = lambda: "2026-01-01T00:00:01+00:00"
    manager._save_registry = lambda: None

    handler = _CaptureHandler()
    logger = logging.getLogger("buddy")
    logger.addHandler(handler)
    configure_logging("buddy-control-plane-test")

    try:
        manager.update_agent_config(
            agent_id,
            """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "Updated"
  model: openrouter:openrouter/free
""",
            restart=False,
        )
    finally:
        logger.removeHandler(handler)

    update_events = [event for event in handler.events if event.get("event") == "managed_agent_update_config_completed"]
    assert len(update_events) == 1
    assert update_events[0]["agent_id"] == agent_id
    assert update_events[0]["restart"] is False
    assert update_events[0]["outcome"] == "success"
    assert "config_yaml" not in update_events[0]
