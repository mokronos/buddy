import os
from typing import cast

from pydantic_ai import Agent

from buddy.a2a.runtime_server import create_runtime_app
from buddy.a2a.server import create_app
from buddy.agent.agent import agents

runtime_mode = os.environ.get("BUDDY_RUNTIME_API_BASE_URL") is not None
runtime_agents = cast(dict[str, Agent], agents) if runtime_mode else {}
app = create_runtime_app(runtime_agents) if runtime_mode else create_app(runtime_agents)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10001)
