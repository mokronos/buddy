from dataclasses import dataclass

from buddy.control_plane.external_agents import ExternalAgentManager
from buddy.control_plane.managed_agents import ManagedAgentManager, ManagedAgentRecord
from buddy.session_store import SessionStore


@dataclass
class ServerState:
    base_url: str
    session_store: SessionStore
    external_agent_manager: ExternalAgentManager
    managed_agent_manager: ManagedAgentManager

    def build_managed_entry(self, record: ManagedAgentRecord) -> dict[str, str | None]:
        mount_path = f"/a2a/managed/{record.agent_id}"
        internal_url: str | None = None
        resolver = getattr(self.managed_agent_manager, "resolve_internal_target", None)
        if callable(resolver):
            try:
                resolved_value = resolver(record.agent_id, record.a2a_mount_path)
                internal_url = resolved_value if isinstance(resolved_value, str) else None
            except ValueError:
                internal_url = None

        return {
            "key": f"managed:{record.agent_id}",
            "name": record.agent_id,
            "mountPath": mount_path,
            "agentCardPath": f"{mount_path}/.well-known/agent-card.json",
            "url": f"{self.base_url}{mount_path}",
            "status": record.status,
            "internalUrl": internal_url,
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
