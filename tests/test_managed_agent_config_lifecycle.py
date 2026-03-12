from pathlib import Path
from threading import Lock

from buddy.control_plane.managed_agents import ManagedAgentManager, ManagedAgentRecord


def test_update_agent_config_restarts_running_agent(tmp_path) -> None:
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

    calls: list[str] = []

    def stop_agent(target_agent_id: str):
        calls.append(f"stop:{target_agent_id}")
        record = manager._records[target_agent_id]
        updated = ManagedAgentRecord(**{**record.__dict__, "status": "stopped"})
        manager._records[target_agent_id] = updated
        return updated

    def start_agent(target_agent_id: str):
        calls.append(f"start:{target_agent_id}")
        record = manager._records[target_agent_id]
        updated = ManagedAgentRecord(**{**record.__dict__, "status": "running"})
        manager._records[target_agent_id] = updated
        return updated

    manager.stop_agent = stop_agent  # type: ignore[method-assign]
    manager.start_agent = start_agent  # type: ignore[method-assign]

    manager.update_agent_config(
        agent_id,
        """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "Updated"
  model: openrouter:openrouter/free
""",
        restart=True,
    )

    assert calls == ["stop:demo-agent", "start:demo-agent"]


def test_update_agent_config_without_restart_keeps_active_runtime_settings(tmp_path) -> None:
    agent_id = "demo-agent"
    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
a2a:
  port: 8000
  mount_path: /a2a
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

    updated = manager.update_agent_config(
        agent_id,
        """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "Updated"
  model: openrouter:openrouter/free
a2a:
  port: 9000
  mount_path: /rpc
""",
        restart=False,
    )

    assert updated.container_port == 8000
    assert updated.a2a_mount_path == "/a2a"
