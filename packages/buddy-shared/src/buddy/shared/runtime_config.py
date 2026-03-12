from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class AgentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1)
    model: str = Field(min_length=1)


class A2ASection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    port: int = Field(default=8000, ge=1, le=65535)
    mount_path: str = Field(default="/a2a", min_length=1)

    @field_validator("mount_path")
    @classmethod
    def validate_mount_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("a2a.mount_path must start with '/'")
        if value != "/" and value.endswith("/"):
            return value.rstrip("/")
        return value


class ToolsSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    web_search: bool = True
    todo: bool = True


class MCPSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    url: str = Field(default="http://127.0.0.1:18001/mcp", min_length=1)


class RuntimeAgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: AgentSection
    a2a: A2ASection = Field(default_factory=A2ASection)
    tools: ToolsSection = Field(default_factory=ToolsSection)
    mcp: MCPSection = Field(default_factory=MCPSection)


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


def dump_runtime_agent_config_yaml(config: RuntimeAgentConfig) -> str:
    payload = config.model_dump(mode="python")
    return yaml.safe_dump(payload, sort_keys=False)


def runtime_rpc_path(mount_path: str) -> str:
    return A2ASection(mount_path=mount_path).mount_path


def runtime_agent_card_path(mount_path: str) -> str:
    normalized_mount_path = runtime_rpc_path(mount_path)
    if normalized_mount_path == "/":
        return "/.well-known/agent-card.json"
    return f"{normalized_mount_path}/.well-known/agent-card.json"


def runtime_extended_card_path(mount_path: str) -> str:
    normalized_mount_path = runtime_rpc_path(mount_path)
    if normalized_mount_path == "/":
        return "/agent/authenticatedExtendedCard"
    return f"{normalized_mount_path}/agent/authenticatedExtendedCard"
