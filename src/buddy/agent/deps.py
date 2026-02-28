from pydantic import BaseModel, ConfigDict

from buddy.environment.manager import EnvironmentManager


class AgentDeps(BaseModel):
    session_id: str
    environment_manager: EnvironmentManager

    model_config = ConfigDict(arbitrary_types_allowed=True)
