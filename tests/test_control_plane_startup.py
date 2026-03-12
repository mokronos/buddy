from dataclasses import dataclass

from fastapi.testclient import TestClient

from buddy.control_plane import server as server_module


@dataclass
class _ManagedRecord:
    agent_id: str
    status: str
    container_id: str | None = None


def test_startup_does_not_create_or_start_a_default_managed_agent(monkeypatch) -> None:
    instances: list[object] = []

    class _FakeManagedAgentManager:
        def __init__(self) -> None:
            self.reconcile_calls = 0
            self.create_calls = 0
            self.start_calls = 0
            self.records: list[_ManagedRecord] = []
            instances.append(self)

        def reconcile_from_docker(self) -> None:
            self.reconcile_calls += 1

        def list_agents(self) -> list[_ManagedRecord]:
            return list(self.records)

        def create_agent(self, **kwargs) -> None:
            self.create_calls += 1

        def start_agent(self, agent_id: str) -> None:
            self.start_calls += 1

    class _FakeExternalAgentManager:
        def list_agents(self) -> list[object]:
            return []

        def get_agent(self, agent_id: str) -> None:
            return None

    monkeypatch.setattr(server_module, "ManagedAgentManager", _FakeManagedAgentManager)
    monkeypatch.setattr(server_module, "ExternalAgentManager", _FakeExternalAgentManager)

    with TestClient(server_module.create_app()):
        pass

    assert len(instances) == 1
    manager = instances[0]
    assert manager.reconcile_calls == 1
    assert manager.create_calls == 0
    assert manager.start_calls == 0


def test_list_agents_does_not_prefer_a_buddy_agent_as_default(monkeypatch) -> None:
    class _FakeManagedAgentManager:
        def __init__(self) -> None:
            self.records = [
                _ManagedRecord(agent_id="alpha", status="stopped"),
                _ManagedRecord(agent_id="buddy", status="stopped"),
            ]

        def reconcile_from_docker(self) -> None:
            return None

        def list_agents(self) -> list[_ManagedRecord]:
            return list(self.records)

    class _FakeExternalAgentManager:
        def list_agents(self) -> list[object]:
            return []

        def get_agent(self, agent_id: str) -> None:
            return None

    monkeypatch.setattr(server_module, "ManagedAgentManager", _FakeManagedAgentManager)
    monkeypatch.setattr(server_module, "ExternalAgentManager", _FakeExternalAgentManager)

    with TestClient(server_module.create_app()) as client:
        response = client.get("/agents")

    assert response.status_code == 200
    assert response.json()["defaultAgentKey"] == "managed:alpha"
