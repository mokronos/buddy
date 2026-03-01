import os
from pathlib import Path
from typing import cast

from pydantic_ai import Agent

from buddy.a2a.runtime_server import create_runtime_app
from buddy.a2a.server import create_app
from buddy.agent.agent import agents
from buddy.agent.config import build_runtime_agents, load_runtime_agent_config

runtime_mode = os.environ.get("BUDDY_RUNTIME_API_BASE_URL") is not None
configured_agents = cast(dict[str, Agent], agents)

if runtime_mode:
    runtime_config_path = os.environ.get("BUDDY_AGENT_CONFIG")
    if not runtime_config_path:
        raise RuntimeError("BUDDY_AGENT_CONFIG is required in runtime mode")
    runtime_config = load_runtime_agent_config(Path(runtime_config_path))
    runtime_agents = build_runtime_agents(runtime_config)
    app = create_runtime_app(cast(dict[str, Agent], runtime_agents))
else:
    app = create_app(configured_agents)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10001)
