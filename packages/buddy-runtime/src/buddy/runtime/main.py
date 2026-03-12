import os
from pathlib import Path
from typing import cast

from buddy.runtime.a2a.server import create_runtime_app
from buddy.runtime.config import build_runtime_agents
from buddy.shared.runtime_config import load_runtime_agent_config
from pydantic_ai import Agent

runtime_config_path = os.environ.get("BUDDY_AGENT_CONFIG")
if not runtime_config_path:
    raise RuntimeError("BUDDY_AGENT_CONFIG is required for runtime agent server")

runtime_config = load_runtime_agent_config(Path(runtime_config_path))
runtime_agents = build_runtime_agents(runtime_config)
app = create_runtime_app(cast(dict[str, Agent], runtime_agents))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
