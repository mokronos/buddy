import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from buddy.control_plane.external_agents import ExternalAgentManager
from buddy.control_plane.managed_agents import ManagedAgentManager
from buddy.control_plane.routes_agents import build_agents_router
from buddy.control_plane.routes_proxy import build_proxy_router
from buddy.control_plane.routes_sessions import build_sessions_router
from buddy.control_plane.server_state import ServerState
from buddy.session_store import SessionStore
from buddy.shared.logging import configure_logging, emit_event, get_logger, request_logging_context
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

load_dotenv()


port = os.environ.get("PORT", 10001)
public_url = os.environ.get("BUDDY_PUBLIC_URL")
base_url = public_url.rstrip("/") if public_url else f"http://localhost:{port}"

if base_url.endswith("/a2a"):
    base_url = base_url[: -len("/a2a")].rstrip("/")


session_store = SessionStore(Path("sessions.db"))
logger = get_logger(__name__)


def create_app() -> FastAPI:
    configure_logging("buddy-control-plane")
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

    @app.middleware("http")
    async def _request_logging_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        request_id_source = "client" if "x-request-id" in request.headers else "generated"
        start_time = perf_counter()
        response: Response | None = None
        error: Exception | None = None

        with request_logging_context(request_id):
            try:
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
            except Exception as exc:
                error = exc
                raise
            else:
                return response
            finally:
                route = request.scope.get("route")
                path_params = request.path_params if request.path_params else request.scope.get("path_params", {})
                agent_id = path_params.get("agent_id") if isinstance(path_params, dict) else None
                proxy_route = getattr(request.state, "proxy_route", None)
                status_code = response.status_code if response is not None else 500
                emit_event(
                    logger,
                    "http_request_completed",
                    level="error" if error is not None or status_code >= 500 else "info",
                    request_id_source=request_id_source,
                    method=request.method,
                    path=request.url.path,
                    route=getattr(route, "path", None),
                    status_code=status_code,
                    duration_ms=round((perf_counter() - start_time) * 1000, 3),
                    outcome=_request_outcome(status_code, error),
                    agent_id=agent_id,
                    agent_kind=_agent_kind_for_request(request.url.path, proxy_route),
                    session_id=path_params.get("session_id") if isinstance(path_params, dict) else None,
                    proxy_path=path_params.get("proxy_path") if isinstance(path_params, dict) else None,
                    proxy_route=proxy_route,
                    proxy_target_url=getattr(request.state, "proxy_target_url", None),
                    streaming=getattr(request.state, "proxy_streaming", None),
                    query_param_keys=sorted(set(request.query_params.keys())),
                    error_type=type(error).__name__ if error is not None else None,
                    error_message=str(error) if error is not None else None,
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
        auto_start_enabled = os.environ.get("BUDDY_MANAGED_AGENT_AUTO_START_ALL", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        started_count = 0
        failed_count = 0
        await run_in_threadpool(managed_agent_manager.reconcile_from_docker)

        if auto_start_enabled:
            records = await run_in_threadpool(managed_agent_manager.list_agents)
            for record in records:
                if record.status == "running":
                    continue
                try:
                    await run_in_threadpool(managed_agent_manager.start_agent, record.agent_id)
                    started_count += 1
                except Exception as error:
                    failed_count += 1
                    emit_event(
                        logger,
                        "managed_agent_autostart_failed",
                        level="error",
                        agent_id=record.agent_id,
                        error_type=type(error).__name__,
                        error_message=str(error),
                        outcome="error",
                    )

        emit_event(
            logger,
            "control_plane_startup_completed",
            auto_start_enabled=auto_start_enabled,
            auto_started_count=started_count,
            auto_start_failed_count=failed_count,
        )

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        stopped_count = 0
        failed_count = 0
        records = await run_in_threadpool(managed_agent_manager.list_agents)
        for record in records:
            if record.container_id and record.status == "running":
                try:
                    await run_in_threadpool(managed_agent_manager.stop_agent, record.agent_id)
                    stopped_count += 1
                except Exception as error:
                    failed_count += 1
                    emit_event(
                        logger,
                        "managed_agent_shutdown_stop_failed",
                        level="error",
                        agent_id=record.agent_id,
                        container_id=record.container_id,
                        outcome="error",
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )

        emit_event(
            logger,
            "control_plane_shutdown_completed",
            stopped_count=stopped_count,
            stop_failed_count=failed_count,
        )

    return app


def _agent_kind_for_request(path: str, proxy_route: str | None) -> str | None:
    if proxy_route == "managed" or path.startswith("/a2a/managed/"):
        return "managed"
    if proxy_route == "external" or path.startswith("/a2a/external/"):
        return "external"
    return None


def _request_outcome(status_code: int, error: Exception | None) -> str:
    if error is not None:
        return "error"
    if status_code >= 500:
        return "error"
    if status_code >= 400:
        return "client_error"
    return "success"
