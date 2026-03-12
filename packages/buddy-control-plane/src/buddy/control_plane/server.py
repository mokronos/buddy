import os
from pathlib import Path

from buddy.control_plane.external_agents import ExternalAgentManager
from buddy.control_plane.managed_agents import ManagedAgentManager
from buddy.control_plane.routes_agents import build_agents_router
from buddy.control_plane.routes_proxy import build_proxy_router
from buddy.control_plane.routes_sessions import build_sessions_router
from buddy.control_plane.server_state import ServerState
from buddy.session_store import SessionStore
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

load_dotenv()


port = os.environ.get("PORT", 10001)
public_url = os.environ.get("BUDDY_PUBLIC_URL")
base_url = public_url.rstrip("/") if public_url else f"http://localhost:{port}"

if base_url.endswith("/a2a"):
    base_url = base_url[: -len("/a2a")].rstrip("/")


session_store = SessionStore(Path("sessions.db"))


def create_app() -> FastAPI:
    app = FastAPI()

    external_agent_manager = ExternalAgentManager()
    managed_agent_manager = ManagedAgentManager()

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    state = ServerState(
        base_url=base_url,
        session_store=session_store,
        external_agent_manager=external_agent_manager,
        managed_agent_manager=managed_agent_manager,
    )

    proxy_connect_timeout_s = float(os.environ.get("BUDDY_A2A_PROXY_CONNECT_TIMEOUT_S", "15"))
    proxy_write_timeout_s = float(os.environ.get("BUDDY_A2A_PROXY_WRITE_TIMEOUT_S", "120"))
    proxy_pool_timeout_s = float(os.environ.get("BUDDY_A2A_PROXY_POOL_TIMEOUT_S", "120"))

    app.include_router(build_sessions_router(state))
    app.include_router(build_agents_router(state))
    app.include_router(
        build_proxy_router(
            state,
            connect_timeout_s=proxy_connect_timeout_s,
            write_timeout_s=proxy_write_timeout_s,
            pool_timeout_s=proxy_pool_timeout_s,
        )
    )

    @app.on_event("startup")
    async def _startup() -> None:
        await run_in_threadpool(managed_agent_manager.reconcile_from_docker)

        if os.environ.get("BUDDY_MANAGED_AGENT_AUTO_START_ALL", "true").strip().lower() in {"1", "true", "yes", "on"}:
            records = await run_in_threadpool(managed_agent_manager.list_agents)
            for record in records:
                if record.status == "running":
                    continue
                try:
                    await run_in_threadpool(managed_agent_manager.start_agent, record.agent_id)
                except Exception as error:
                    print(f"Failed to auto-start managed agent '{record.agent_id}' during startup: {error}")

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        records = await run_in_threadpool(managed_agent_manager.list_agents)
        for record in records:
            if record.container_id and record.status == "running":
                try:
                    await run_in_threadpool(managed_agent_manager.stop_agent, record.agent_id)
                except Exception as error:
                    print(f"Failed to stop managed agent '{record.agent_id}' during shutdown: {error}")

    return app
