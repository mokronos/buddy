from pathlib import Path
from threading import Lock

import pytest

from buddy.control_plane.managed_agents import ManagedAgentManager


def test_create_agent_rolls_back_registry_and_config_when_start_fails(tmp_path) -> None:
    agent_id = "demo-agent"
    config_path = tmp_path / "agents" / agent_id / "agent.yaml"

    manager = object.__new__(ManagedAgentManager)
    manager._lock = Lock()
    manager._records = {}
    manager._registry_path = Path(tmp_path / "registry.json")
    manager._now = lambda: "2026-01-01T00:00:00+00:00"
    manager._save_registry = lambda: None
    manager._validate_config = lambda *_args, **_kwargs: None

    def write_config(_agent_id: str, config_yaml: str) -> Path:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(config_yaml, encoding="utf-8")
        return config_path

    manager._write_config = write_config
    manager._start_container = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("readiness failed"))

    with pytest.raises(RuntimeError, match="readiness failed"):
        manager.create_agent(
            agent_id=agent_id,
            image="buddy-agent-runtime:latest",
            config_yaml="""agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
""",
            container_port=8000,
            config_mount_path="/etc/buddy/agent.yaml",
            extra_env={},
            command=None,
        )

    assert manager._records == {}
    assert not config_path.exists()
