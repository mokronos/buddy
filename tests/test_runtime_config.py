import pytest
from buddy.shared.runtime_config import (
    dump_runtime_agent_config_yaml,
    parse_runtime_agent_config_yaml,
    runtime_agent_card_path,
    runtime_extended_card_path,
    runtime_rpc_path,
)


def test_parse_runtime_config_valid() -> None:
    config = parse_runtime_agent_config_yaml(
        """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
mcp_servers:
  - url: http://127.0.0.1:18001/mcp
  - url: http://127.0.0.1:18002/mcp
"""
    )
    assert config.agent.id == "demo-agent"
    assert [server.url for server in config.mcp_servers] == [
        "http://127.0.0.1:18001/mcp",
        "http://127.0.0.1:18002/mcp",
    ]


def test_parse_runtime_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError):
        parse_runtime_agent_config_yaml(
            """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
unexpected: true
"""
        )


def test_parse_runtime_config_rejects_removed_environment_tools_section() -> None:
    with pytest.raises(ValueError):
        parse_runtime_agent_config_yaml(
            """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
a2a:
  port: 9000
"""
        )


def test_parse_runtime_config_normalizes_a2a_mount_path() -> None:
    assert runtime_rpc_path("/rpc/") == "/rpc"


def test_dump_runtime_config_yaml_preserves_mcp_servers() -> None:
    config = parse_runtime_agent_config_yaml(
        """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
mcp_servers:
  - url: http://example.com/mcp
"""
    )

    dumped = dump_runtime_agent_config_yaml(config)

    assert "mcp_servers:" in dumped
    assert "- url: http://example.com/mcp" in dumped


def test_runtime_path_helpers_handle_root_and_prefixed_mounts() -> None:
    assert runtime_agent_card_path("/") == "/.well-known/agent-card.json"
    assert runtime_agent_card_path("/a2a") == "/a2a/.well-known/agent-card.json"
    assert runtime_extended_card_path("/") == "/agent/authenticatedExtendedCard"
    assert runtime_extended_card_path("/a2a") == "/a2a/agent/authenticatedExtendedCard"
