from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class AgentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1)
    model: str = Field(min_length=1)


class A2ASection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    port: int = Field(default=10001, ge=1, le=65535)
    mount_path: str = Field(default="/a2a", min_length=1)


class ToolEnvironmentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    image: str | None = None
    warm_containers: int | None = Field(default=None, ge=0)


class ToolsSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    web_search: bool = True
    todo: bool = True
    environment: bool | ToolEnvironmentSection = True


class RuntimeAgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: AgentSection
    a2a: A2ASection = Field(default_factory=A2ASection)
    tools: ToolsSection = Field(default_factory=ToolsSection)

    def environment_enabled(self) -> bool:
        environment = self.tools.environment
        if isinstance(environment, bool):
            return environment
        return environment.enabled


def parse_runtime_agent_config_yaml(config_yaml: str) -> RuntimeAgentConfig:
    try:
        payload = yaml.safe_load(config_yaml)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid runtime config YAML: {error}") from error

    if not isinstance(payload, dict):
        raise TypeError("Invalid runtime config YAML: top-level value must be a mapping")

    try:
        return RuntimeAgentConfig.model_validate(payload)
    except ValidationError as error:
        raise ValueError(f"Invalid runtime config YAML: {error}") from error


def load_runtime_agent_config(config_path: Path) -> RuntimeAgentConfig:
    if not config_path.exists():
        raise ValueError(f"Runtime config file does not exist: {config_path}")
    raw_yaml = config_path.read_text(encoding="utf-8")
    return parse_runtime_agent_config_yaml(raw_yaml)
