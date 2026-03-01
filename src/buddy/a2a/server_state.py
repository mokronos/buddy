from dataclasses import dataclass

from buddy.a2a.external_agents import ExternalAgentManager
from buddy.a2a.managed_agents import ManagedAgentManager
from buddy.environment.manager import EnvironmentManager
from buddy.session_store import SessionStore


@dataclass
class ServerState:
    base_url: str
    session_store: SessionStore
    external_agent_manager: ExternalAgentManager
    managed_agent_manager: ManagedAgentManager | None
    local_environment_manager: EnvironmentManager | None
    default_agent_key: str | None
    agent_index: list[dict[str, str]]
    internal_runtime_token: str | None

    def build_managed_entry(self, agent_id: str, status: str) -> dict[str, str]:
        mount_path = f"/a2a/managed/{agent_id}"
        return {
            "key": f"managed:{agent_id}",
            "name": agent_id,
            "mountPath": mount_path,
            "agentCardPath": f"{mount_path}/.well-known/agent-card.json",
            "url": f"{self.base_url}{mount_path}",
            "status": status,
        }

    def build_external_entry(self, agent_id: str) -> dict[str, str]:
        record = self.external_agent_manager.get_agent(agent_id)
        if record is None:
            raise ValueError(f"External agent '{agent_id}' not found")
        mount_path = f"/a2a/external/{agent_id}"
        card_file = "agent.json" if record.use_legacy_card_path else "agent-card.json"
        return {
            "key": f"external:{agent_id}",
            "name": agent_id,
            "mountPath": mount_path,
            "agentCardPath": f"{mount_path}/.well-known/{card_file}",
            "url": f"{self.base_url}{mount_path}",
            "status": "registered",
        }
