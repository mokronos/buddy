import pytest
from buddy.shared.runtime_config import parse_runtime_agent_config_yaml


def test_parse_runtime_config_valid() -> None:
    config = parse_runtime_agent_config_yaml(
        """agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are helpful"
  model: openrouter:openrouter/free
tools:
  web_search: true
  todo: false
"""
    )
    assert config.agent.id == "demo-agent"
    assert config.a2a.port == 8000
    assert config.tools.web_search is True
    assert config.tools.todo is False


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
tools:
  environment: true
"""
        )
