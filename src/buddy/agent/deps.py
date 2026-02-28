from pydantic import BaseModel, ConfigDict

from buddy.environment.runtime import EnvironmentRuntime


class AgentDeps(BaseModel):
    session_id: str
    environment_manager: EnvironmentRuntime

    model_config = ConfigDict(arbitrary_types_allowed=True)
