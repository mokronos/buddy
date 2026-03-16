from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


DEFAULT_RUNTIME_IMAGE = "buddy-agent-runtime:latest"
DEFAULT_RUNTIME_CONFIG_MOUNT_PATH = "/etc/buddy/agent.yaml"
DEFAULT_RUNTIME_A2A_PORT = 8000
DEFAULT_RUNTIME_A2A_MOUNT_PATH = "/a2a"
DEFAULT_MCP_SERVER_URL = "http://127.0.0.1:18001/mcp"


class AgentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1)
    model: str = Field(min_length=1)


SYSTEM_AGENT_INSTRUCTIONS_GENERAL = """You are a helpful AI assistant with access to tools.

## Tool Usage Guidelines
- Use tools proactively to help the user accomplish their goals
- When you need to perform actions (like sending messages, creating tasks, or searching), use the appropriate tools
- You can use multiple tools in parallel when their results are independent
- Always explain what you're doing when using tools, especially for actions that modify state

## Communication
- Be concise and direct in your responses
- If you encounter errors, explain them clearly and suggest alternatives
- When tasks require multiple steps, summarize your progress

## Limitations
- If you don't have enough information, ask clarifying questions instead of guessing
- Don't make assumptions about external systems or data that you don't have access to
"""


SYSTEM_AGENT_INSTRUCTIONS_SKILL_USAGE = """## Skill Usage
In your environment, you have skills available at ~/.agents/skills/*.
Use the read tool to load a skill's file when the task matches its description.
"""


class A2ASection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    port: int = Field(default=DEFAULT_RUNTIME_A2A_PORT, ge=1, le=65535)
    mount_path: str = Field(default=DEFAULT_RUNTIME_A2A_MOUNT_PATH, min_length=1)

    @field_validator("mount_path")
    @classmethod
    def validate_mount_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("a2a.mount_path must start with '/'")
        if value != "/" and value.endswith("/"):
            return value.rstrip("/")
        return value


class MCPServerSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("mcp server url is required")
        return trimmed


class UserAgentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1)
    model: str = Field(min_length=1)


class UserRuntimeAgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: UserAgentSection
    mcp_servers: list[MCPServerSection] = Field(default_factory=lambda: [MCPServerSection(url=DEFAULT_MCP_SERVER_URL)])


class RuntimeAgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: AgentSection
    mcp_servers: list[MCPServerSection] = Field(default_factory=lambda: [MCPServerSection(url=DEFAULT_MCP_SERVER_URL)])
    default_instructions: str = Field(default="")


def build_runtime_agent_config(user_config: UserRuntimeAgentConfig, *, agent_id: str) -> RuntimeAgentConfig:
    return RuntimeAgentConfig(
        agent=AgentSection(
            id=agent_id,
            name=user_config.agent.name,
            instructions=user_config.agent.instructions,
            model=user_config.agent.model,
        ),
        mcp_servers=user_config.mcp_servers,
        default_instructions=SYSTEM_AGENT_INSTRUCTIONS_GENERAL + "\n\n" + SYSTEM_AGENT_INSTRUCTIONS_SKILL_USAGE,
    )


def to_user_runtime_agent_config(config: RuntimeAgentConfig) -> UserRuntimeAgentConfig:
    return UserRuntimeAgentConfig(
        agent=UserAgentSection(
            name=config.agent.name,
            instructions=config.agent.instructions,
            model=config.agent.model,
        ),
        mcp_servers=config.mcp_servers,
    )


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
