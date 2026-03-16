from buddy.shared.runtime_config import RuntimeAgentConfig
from pydantic_ai import Agent


def build_runtime_agents(config: RuntimeAgentConfig) -> dict[str, Agent[None, str]]:
    from buddy.runtime.agent import create_agent

    instructions = config.default_instructions
    if config.agent.instructions:
        if instructions:
            instructions = f"{instructions}\n\n---\n\n{config.agent.instructions}"
        else:
            instructions = config.agent.instructions

    agent = create_agent(
        name=config.agent.name,
        instructions=instructions,
        model=config.agent.model,
        mcp_server_urls=[server.url for server in config.mcp_servers],
    )
    return {config.agent.id: agent}
