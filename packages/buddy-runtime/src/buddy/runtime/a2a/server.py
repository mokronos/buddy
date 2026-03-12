import os
from pathlib import Path

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard
from buddy.runtime.a2a.executor import PyAIAgentExecutor
from buddy.shared.runtime_config import runtime_agent_card_path, runtime_extended_card_path, runtime_rpc_path
from buddy.session_store import SessionStore
from devtools import pprint
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic_ai import Agent

load_dotenv()


session_store = SessionStore(Path("sessions.db"))


def _create_agent_card(name: str, url: str) -> AgentCard:
    return AgentCard(
        name=name,
        description=name,
        url=url,
        capabilities=AgentCapabilities(
            streaming=True,
        ),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[],
        version="0.0.1",
    )


def _create_a2a_runtime_app(
    agent: Agent,
    card_name: str,
    card_url: str,
    mount_path: str,
) -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=PyAIAgentExecutor(
            agent=agent,
            session_store=session_store,
        ),
        task_store=InMemoryTaskStore(),
    )

    agent_card = _create_agent_card(card_name, card_url)
    pprint(agent_card)
    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)

    return a2a_app.build(
        agent_card_url=runtime_agent_card_path(mount_path),
        rpc_url=runtime_rpc_path(mount_path),
        extended_agent_card_url=runtime_extended_card_path(mount_path),
    )


def create_runtime_app(agents: dict[str, Agent], *, port: int, mount_path: str) -> FastAPI:
    if not agents:
        raise RuntimeError("Runtime app requires at least one configured agent")

    normalized_mount_path = runtime_rpc_path(mount_path)
    public_url = os.environ.get("BUDDY_PUBLIC_URL")
    base_url = public_url.rstrip("/") if public_url else f"http://localhost:{port}"
    if normalized_mount_path != "/" and base_url.endswith(normalized_mount_path):
        base_url = base_url[: -len(normalized_mount_path)].rstrip("/")

    agent_key = next(iter(agents.keys()))
    agent = agents[agent_key]
    card_name = agent.name or agent_key

    app = _create_a2a_runtime_app(
        agent=agent,
        card_name=card_name,
        card_url=f"{base_url}{normalized_mount_path}" if normalized_mount_path != "/" else base_url,
        mount_path=normalized_mount_path,
    )

    return app
