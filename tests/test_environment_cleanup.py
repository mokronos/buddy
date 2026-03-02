from collections import deque

import pytest
from docker.errors import NotFound

from buddy.environment.manager import EnvironmentManager


class FakeContainer:
    def __init__(self, fake_docker: "FakeDocker", container_id: str, name: str) -> None:
        self._fake_docker = fake_docker
        self.id = container_id
        self.name = name

    def reload(self) -> None:
        return None

    def remove(self, force: bool = True) -> None:
        self._fake_docker.remove(self.id)


class FakeContainers:
    def __init__(self, fake_docker: "FakeDocker") -> None:
        self._fake_docker = fake_docker

    def get(self, identifier: str) -> FakeContainer:
        container = self._fake_docker.by_id.get(identifier)
        if container is not None:
            return container
        for candidate in self._fake_docker.by_id.values():
            if candidate.name == identifier:
                return candidate
        raise NotFound("container not found")


class FakeDocker:
    def __init__(self) -> None:
        self.by_id: dict[str, FakeContainer] = {}
        self.containers = FakeContainers(self)

    def add(self, container_id: str, name: str) -> None:
        self.by_id[container_id] = FakeContainer(self, container_id, name)

    def remove(self, container_id: str) -> None:
        self.by_id.pop(container_id, None)


def test_release_managed_agent_containers_removes_matching_leases_and_idle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_docker = FakeDocker()
    monkeypatch.setattr("buddy.environment.manager.docker.from_env", lambda: fake_docker)

    manager = EnvironmentManager(image_ref="unused")

    fake_docker.add("lease-match", "buddy-env-agent-managed-teest-1")
    fake_docker.add("lease-keep", "buddy-env-other-1")
    fake_docker.add("idle-match", "buddy-env-agent-managed-teest-2")
    fake_docker.add("idle-keep", "buddy-env-generic-1")

    manager._leases = {
        "agent-managed-teest:agent-managed-teest--ctx-1": "lease-match",
        "agent-external-foo:agent-external-foo--ctx-1": "lease-keep",
    }
    manager._idle = deque(["idle-match", "idle-keep"])

    removed = manager.release_managed_agent_containers("teest")

    assert removed == 2
    assert "agent-managed-teest:agent-managed-teest--ctx-1" not in manager._leases
    assert manager._leases["agent-external-foo:agent-external-foo--ctx-1"] == "lease-keep"
    assert list(manager._idle) == ["idle-keep"]
    assert "lease-match" not in fake_docker.by_id
    assert "idle-match" not in fake_docker.by_id
