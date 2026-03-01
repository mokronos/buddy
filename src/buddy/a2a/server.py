import os
from pathlib import Path

import requests
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard
from devtools import pprint
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from buddy.a2a.executor import PyAIAgentExecutor
from buddy.a2a.managed_agents import ManagedAgentManager
from buddy.environment.manager import EnvironmentManager
from buddy.environment.runtime import EnvironmentRuntime
from buddy.environment.runtime_api import RuntimeAPIEnvironmentManager
from buddy.session_store import SessionStore

load_dotenv()


port = os.environ.get("PORT", 10001)
public_url = os.environ.get("BUDDY_PUBLIC_URL")
base_url = public_url.rstrip("/") if public_url else f"http://localhost:{port}"

if base_url.endswith("/a2a"):
    base_url = base_url[: -len("/a2a")].rstrip("/")


session_store = SessionStore(Path("sessions.db"))


def _int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


internal_runtime_token = os.environ.get("BUDDY_INTERNAL_RUNTIME_TOKEN")


class ManagedAgentCreateRequest(BaseModel):
    agent_id: str
    image: str = "buddy-agent-runtime:latest"
    config_yaml: str
    container_port: int = 10001
    config_mount_path: str = "/etc/buddy/agent.yaml"
    env: dict[str, str] = Field(default_factory=dict)
    command: list[str] | None = None


class ManagedAgentStartRequest(BaseModel):
    env: dict[str, str] = Field(default_factory=dict)
    command: list[str] | None = None


class RuntimeAcquireRequest(BaseModel):
    owner_id: str


class RuntimeReleaseRequest(BaseModel):
    owner_id: str
    reusable: bool = True


class RuntimeExecRequest(BaseModel):
    owner_id: str
    command: str
    timeout_s: int = 30


class RuntimeReadFileRequest(BaseModel):
    owner_id: str
    path: str


class RuntimeWriteFileRequest(BaseModel):
    owner_id: str
    path: str
    content: str


class RuntimePatchFileRequest(BaseModel):
    owner_id: str
    path: str
    old_text: str
    new_text: str
    count: int = 1


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


def _create_a2a_sub_app(
    agent: Agent,
    card_name: str,
    card_url: str,
    manager: EnvironmentRuntime,
) -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=PyAIAgentExecutor(
            agent=agent,
            session_store=session_store,
            environment_manager=manager,
        ),
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
    agent_index: list[dict[str, str]] = []
    runtime_api_base_url = os.environ.get("BUDDY_RUNTIME_API_BASE_URL")

    if runtime_api_base_url:
        agent_environment_runtime = RuntimeAPIEnvironmentManager(
            base_url=runtime_api_base_url,
            token=internal_runtime_token,
        )
        local_environment_manager: EnvironmentManager | None = None
        managed_agent_manager: ManagedAgentManager | None = None
    else:
        local_environment_manager = EnvironmentManager(
            image_ref=os.environ.get("BUDDY_ENV_IMAGE", "environ:latest"),
            warm_containers=_int_env("BUDDY_ENV_WARM_CONTAINERS", 1),
        )
        agent_environment_runtime = local_environment_manager
        managed_agent_manager = ManagedAgentManager()

    def _build_managed_entry(agent_id: str, status: str) -> dict[str, str]:
        mount_path = f"/a2a/managed/{agent_id}"
        return {
            "key": f"managed:{agent_id}",
            "name": agent_id,
            "mountPath": mount_path,
            "agentCardPath": f"{mount_path}/.well-known/agent-card.json",
            "url": f"{base_url}{mount_path}",
            "status": status,
        }

    def _ensure_internal_auth(request: Request) -> None:
        if not internal_runtime_token:
            return
        provided = request.headers.get("x-buddy-internal-token")
        if provided != internal_runtime_token:
            raise HTTPException(status_code=401, detail="Unauthorized internal runtime request")

    def _fetch_managed_runtime_routes(agent_id: str) -> tuple[str, str]:
        target_base = managed_agent_manager.resolve_target(agent_id, "/")
        try:
            response = requests.get(f"{target_base.rstrip('/')}/agents", timeout=5)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as error:
            raise HTTPException(
                status_code=502, detail=f"Managed agent '{agent_id}' is unreachable: {error}"
            ) from error

        if not isinstance(payload, dict):
            raise HTTPException(status_code=502, detail=f"Managed agent '{agent_id}' returned invalid /agents payload")

        agents_payload = payload.get("agents")
        default_key = payload.get("defaultAgentKey")
        if not isinstance(agents_payload, list) or not agents_payload:
            raise HTTPException(status_code=502, detail=f"Managed agent '{agent_id}' reported no available agents")

        selected = None
        for entry in agents_payload:
            if not isinstance(entry, dict):
                continue
            key = entry.get("key")
            if isinstance(default_key, str) and key == default_key:
                selected = entry
                break
        if selected is None:
            selected = agents_payload[0] if isinstance(agents_payload[0], dict) else None
        if selected is None:
            raise HTTPException(status_code=502, detail=f"Managed agent '{agent_id}' has invalid agent metadata")

        mount_path = selected.get("mountPath")
        card_path = selected.get("agentCardPath")
        if not isinstance(mount_path, str) or not isinstance(card_path, str):
            raise HTTPException(status_code=502, detail=f"Managed agent '{agent_id}' missing mount/card paths")

        return mount_path, card_path

    @app.on_event("startup")
    async def _startup() -> None:
        if local_environment_manager is not None:
            local_environment_manager.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        if local_environment_manager is not None:
            local_environment_manager.stop()

    for agent_key, agent in agents.items():
        mount_path = f"/a2a/{agent_key}"
        card_url = f"{base_url}{mount_path}"
        card_name = agent.name or f"buddy-{agent_key}"
        sub_app = _create_a2a_sub_app(
            agent=agent,
            card_name=card_name,
            card_url=card_url,
            manager=agent_environment_runtime,
        )
        app.mount(mount_path, sub_app)
        agent_index.append({
            "key": agent_key,
            "name": card_name,
            "mountPath": mount_path,
            "agentCardPath": f"{mount_path}/.well-known/agent-card.json",
            "url": card_url,
        })

    default_agent_key = "buddy" if any(item["key"] == "buddy" for item in agent_index) else None
    if default_agent_key is None and agent_index:
        default_agent_key = agent_index[0]["key"]

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

    @app.get("/agents")
    async def list_agents() -> JSONResponse:
        managed_entries = (
            [_build_managed_entry(record.agent_id, record.status) for record in managed_agent_manager.list_agents()]
            if managed_agent_manager is not None
            else []
        )
        all_entries = [*agent_index, *managed_entries]
        default_key = default_agent_key
        if default_key is None and all_entries:
            default_key = all_entries[0]["key"]
        return JSONResponse({
            "defaultAgentKey": default_key,
            "agents": all_entries,
            "managedAgents": managed_entries,
        })

    @app.get("/managed-agents")
    async def list_managed_agents() -> JSONResponse:
        if managed_agent_manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")
        agents_payload = [record.__dict__ for record in managed_agent_manager.list_agents()]
        return JSONResponse({"agents": agents_payload})

    @app.get("/managed-agents/{agent_id}")
    async def get_managed_agent(agent_id: str) -> JSONResponse:
        if managed_agent_manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")
        record = managed_agent_manager.get_agent(agent_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Managed agent '{agent_id}' not found")
        return JSONResponse({"agent": record.__dict__})

    @app.post("/managed-agents")
    async def create_managed_agent(payload: ManagedAgentCreateRequest) -> JSONResponse:
        if managed_agent_manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")
        try:
            record = managed_agent_manager.create_agent(
                agent_id=payload.agent_id,
                image=payload.image,
                config_yaml=payload.config_yaml,
                container_port=payload.container_port,
                config_mount_path=payload.config_mount_path,
                extra_env=payload.env,
                command=payload.command,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {error}") from error

        mount_path = f"/a2a/managed/{record.agent_id}"
        return JSONResponse(
            {
                "agent": record.__dict__,
                "proxyBaseUrl": f"{base_url}{mount_path}",
                "agentCardUrl": f"{base_url}{mount_path}/.well-known/agent-card.json",
            },
            status_code=201,
        )

    @app.post("/managed-agents/{agent_id}/start")
    async def start_managed_agent(agent_id: str, payload: ManagedAgentStartRequest) -> JSONResponse:
        if managed_agent_manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")
        try:
            record = managed_agent_manager.start_agent(
                agent_id,
                extra_env=payload.env,
                command=payload.command,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Failed to start agent: {error}") from error
        return JSONResponse({"agent": record.__dict__})

    @app.post("/managed-agents/{agent_id}/stop")
    async def stop_managed_agent(agent_id: str) -> JSONResponse:
        if managed_agent_manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")
        try:
            record = managed_agent_manager.stop_agent(agent_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return JSONResponse({"agent": record.__dict__})

    @app.delete("/managed-agents/{agent_id}")
    async def delete_managed_agent(agent_id: str, request: Request) -> JSONResponse:
        if managed_agent_manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")
        remove_config = request.query_params.get("removeConfig") == "true"
        try:
            managed_agent_manager.delete_agent(agent_id, remove_config=remove_config)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return JSONResponse({"ok": True})

    @app.api_route(
        "/a2a/managed/{agent_id}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    @app.api_route(
        "/a2a/managed/{agent_id}/{proxy_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def proxy_managed_agent(agent_id: str, request: Request, proxy_path: str = "") -> Response:
        if managed_agent_manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")
        try:
            mount_path, card_path = _fetch_managed_runtime_routes(agent_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        proxy_root = f"{base_url}/a2a/managed/{agent_id}"
        if proxy_path == ".well-known/agent-card.json":
            upstream_card_url = managed_agent_manager.resolve_target(agent_id, card_path)
            try:
                card_response = requests.get(upstream_card_url, timeout=15)
                card_response.raise_for_status()
                card = card_response.json()
            except requests.RequestException as error:
                raise HTTPException(status_code=502, detail=f"Failed to fetch managed agent card: {error}") from error

            if isinstance(card, dict):
                card["url"] = proxy_root
            return JSONResponse(card)

        relative_path = proxy_path.strip("/")
        upstream_path = f"{mount_path.rstrip('/')}/{relative_path}" if relative_path else mount_path

        try:
            target_url = managed_agent_manager.resolve_target(agent_id, upstream_path)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        raw_headers = dict(request.headers)
        raw_headers.pop("host", None)
        raw_headers.pop("content-length", None)
        body = await request.body()
        query_params = list(request.query_params.multi_items())

        upstream = requests.request(
            method=request.method,
            url=target_url,
            params=query_params,
            headers=raw_headers,
            data=body,
            timeout=120,
        )

        excluded = {"content-length", "transfer-encoding", "connection", "content-encoding"}
        passthrough_headers = {key: value for key, value in upstream.headers.items() if key.lower() not in excluded}
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=passthrough_headers,
            media_type=upstream.headers.get("content-type"),
        )

    @app.post("/internal/runtime/acquire")
    async def runtime_acquire(payload: RuntimeAcquireRequest, request: Request) -> JSONResponse:
        if local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        _ensure_internal_auth(request)
        lease = local_environment_manager.acquire(payload.owner_id)
        return JSONResponse({"ownerId": lease.owner_id, "containerId": lease.container_id})

    @app.post("/internal/runtime/release")
    async def runtime_release(payload: RuntimeReleaseRequest, request: Request) -> JSONResponse:
        if local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        _ensure_internal_auth(request)
        local_environment_manager.release(payload.owner_id, reusable=payload.reusable)
        return JSONResponse({"ok": True})

    @app.post("/internal/runtime/exec")
    async def runtime_exec(payload: RuntimeExecRequest, request: Request) -> JSONResponse:
        if local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        _ensure_internal_auth(request)
        result = local_environment_manager.exec(
            owner_id=payload.owner_id,
            command=payload.command,
            timeout_s=payload.timeout_s,
        )
        return JSONResponse({
            "exitCode": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })

    @app.post("/internal/runtime/read-file")
    async def runtime_read_file(payload: RuntimeReadFileRequest, request: Request) -> JSONResponse:
        if local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        _ensure_internal_auth(request)
        try:
            content = local_environment_manager.read_file(payload.owner_id, payload.path)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return JSONResponse({"content": content})

    @app.post("/internal/runtime/write-file")
    async def runtime_write_file(payload: RuntimeWriteFileRequest, request: Request) -> JSONResponse:
        if local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        _ensure_internal_auth(request)
        try:
            local_environment_manager.write_file(payload.owner_id, payload.path, payload.content)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return JSONResponse({"ok": True})

    @app.post("/internal/runtime/patch-file")
    async def runtime_patch_file(payload: RuntimePatchFileRequest, request: Request) -> JSONResponse:
        if local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        _ensure_internal_auth(request)
        try:
            replacements = local_environment_manager.patch_file(
                owner_id=payload.owner_id,
                path=payload.path,
                old_text=payload.old_text,
                new_text=payload.new_text,
                count=payload.count,
            )
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return JSONResponse({"ok": True, "replacements": replacements})

    return app
