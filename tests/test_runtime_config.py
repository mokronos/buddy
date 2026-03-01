import pytest

from buddy.agent.config import parse_runtime_agent_config_yaml


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
  environment:
    enabled: true
"""
    )
    assert config.agent.id == "demo-agent"
    assert config.tools.web_search is True
    assert config.tools.todo is False
    assert config.environment_enabled() is True


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
