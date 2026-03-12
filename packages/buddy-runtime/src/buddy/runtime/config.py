from buddy.shared.runtime_config import RuntimeAgentConfig
from pydantic_ai import Agent


def build_runtime_agents(config: RuntimeAgentConfig) -> dict[str, Agent[None, str]]:
    from buddy.runtime.agent import create_agent

    agent = create_agent(
        name=config.agent.name,
        instructions=config.agent.instructions,
        model=config.agent.model,
        enable_web_search=config.tools.web_search,
        enable_todo=config.tools.todo,
    )
    return {config.agent.id: agent}
