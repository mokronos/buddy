from dataclasses import dataclass

from buddy.environment.runtime import EnvironmentRuntime


@dataclass
class AgentDeps:
    session_id: str
    environment_owner_id: str
    environment_manager: EnvironmentRuntime
