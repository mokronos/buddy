import os
from pathlib import Path

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard
from devtools import pprint
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_ai import Agent

from buddy.a2a.executor import PyAIAgentExecutor
from buddy.session_store import SessionStore

load_dotenv()


port = os.environ.get("PORT", 10001)
public_url = os.environ.get("BUDDY_PUBLIC_URL")
base_url = public_url.rstrip("/") if public_url else f"http://localhost:{port}"

if base_url.endswith("/a2a"):
    base_url = base_url[: -len("/a2a")].rstrip("/")


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


def _create_a2a_sub_app(agent: Agent, card_name: str, card_url: str) -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=PyAIAgentExecutor(agent=agent, session_store=session_store),
        task_store=InMemoryTaskStore(),
    )

    agent_card = _create_agent_card(card_name, card_url)
    pprint(agent_card)
    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)

    return a2a_app.build(
        agent_card_url="/.well-known/agent-card.json",
        rpc_url="/",
        extended_agent_card_url="/agent/authenticatedExtendedCard",
    )


def create_app(agents: dict[str, Agent]) -> FastAPI:
    app = FastAPI()
    mounted_sub_apps: dict[str, FastAPI] = {}

    for agent_key, agent in agents.items():
        mount_path = f"/a2a/{agent_key}"
        card_url = f"{base_url}{mount_path}"
        card_name = agent.name or f"buddy-{agent_key}"
        sub_app = _create_a2a_sub_app(agent=agent, card_name=card_name, card_url=card_url)
        app.mount(mount_path, sub_app)
        mounted_sub_apps[agent_key] = sub_app

    if mounted_sub_apps:
        first_agent_key = next(iter(mounted_sub_apps))
        app.mount("/a2a", mounted_sub_apps[first_agent_key])

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/sessions")
    async def list_sessions(request: Request) -> JSONResponse:
        limit_param = request.query_params.get("limit")
        limit = int(limit_param) if limit_param and limit_param.isdigit() else 20
        sessions = session_store.list_sessions(limit)
        return JSONResponse({"sessions": sessions})

    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str) -> JSONResponse:
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session id")
        session = session_store.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return JSONResponse({
            "session": session,
            "messages": session_store.load_chat_messages(session_id),
            "events": session_store.load_events(session_id),
        })

    return app
