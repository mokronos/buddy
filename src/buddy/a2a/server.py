import os
import os
from pathlib import Path

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard
from devtools import pprint
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic_ai import Agent

from buddy.a2a.executor import PyAIAgentExecutor
from buddy.session_store import SessionStore

load_dotenv()


port = os.environ.get("PORT", 10001)
public_url = os.environ.get("BUDDY_PUBLIC_URL")
base_url = public_url.rstrip("/") if public_url else f"http://localhost:{port}"

if base_url.endswith("/a2a"):
    a2a_base_url = base_url
    base_url = base_url[: -len("/a2a")].rstrip("/")
else:
    a2a_base_url = f"{base_url}/a2a"


session_store = SessionStore(Path("sessions.db"))


agent_card = AgentCard(
    name="Test Agent",
    description="Test Agent",
    url=a2a_base_url,
    capabilities=AgentCapabilities(
        streaming=True,
    ),
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[],
    version="0.0.1",
)

pprint(agent_card)


def create_app(agent: Agent) -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=PyAIAgentExecutor(agent=agent, session_store=session_store),
        task_store=InMemoryTaskStore(),
    )

    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)

    app = a2a_app.build(
        agent_card_url="/a2a/.well-known/agent-card.json",
        rpc_url="/a2a",
        extended_agent_card_url="/a2a/agent/authenticatedExtendedCard",
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
