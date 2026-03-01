import os
from pathlib import Path
from urllib.parse import urlparse

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai import Agent
from starlette.concurrency import run_in_threadpool

from buddy.a2a.executor import PyAIAgentExecutor
from buddy.a2a.external_agents import ExternalAgentManager
from buddy.a2a.managed_agents import ManagedAgentManager
from buddy.a2a.routes_agents import build_agents_router
from buddy.a2a.routes_proxy import build_proxy_router
from buddy.a2a.routes_runtime import build_runtime_router
from buddy.a2a.routes_sessions import build_sessions_router
from buddy.a2a.server_state import ServerState
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


def _bool_env(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _default_managed_agent_yaml() -> str:
    return """agent:
  id: buddy
  name: buddy
  instructions: \"You are the English Buddy agent. Reply in English only.\"
  model: openrouter:openrouter/free

a2a:
  port: 10001
"""


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
    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)

    return a2a_app.build(
        agent_card_url="/.well-known/agent-card.json",
        rpc_url="/",
        extended_agent_card_url="/agent/authenticatedExtendedCard",
    )


def _is_local_or_dev_mode(current_base_url: str) -> bool:
    env_name = os.environ.get("BUDDY_ENV", "").strip().lower()
    if env_name in {"dev", "development", "local", "test"}:
        return True

    allow_insecure_internal = os.environ.get("BUDDY_ALLOW_INSECURE_INTERNAL_RUNTIME", "false")
    if allow_insecure_internal.strip().lower() in {"1", "true", "yes", "on"}:
        return True

    try:
        parsed = urlparse(current_base_url)
    except ValueError:
        return False

    return parsed.hostname in {"localhost", "127.0.0.1"}


def _enforce_internal_token_policy(current_base_url: str, token: str | None) -> None:
    if token:
        return
    if _is_local_or_dev_mode(current_base_url):
        return
    raise RuntimeError(
        "BUDDY_INTERNAL_RUNTIME_TOKEN is required in non-local environments. "
        "Set the token or explicitly opt into insecure mode with BUDDY_ALLOW_INSECURE_INTERNAL_RUNTIME=true."
    )


def create_app(agents: dict[str, Agent]) -> FastAPI:
    app = FastAPI()
    runtime_api_base_url = os.environ.get("BUDDY_RUNTIME_API_BASE_URL")
    internal_runtime_token = os.environ.get("BUDDY_INTERNAL_RUNTIME_TOKEN")
    _enforce_internal_token_policy(base_url, internal_runtime_token)

    external_agent_manager = ExternalAgentManager()

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

    agent_index: list[dict[str, str]] = []
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

    state = ServerState(
        base_url=base_url,
        session_store=session_store,
        external_agent_manager=external_agent_manager,
        managed_agent_manager=managed_agent_manager,
        local_environment_manager=local_environment_manager,
        default_agent_key=default_agent_key,
        agent_index=agent_index,
        internal_runtime_token=internal_runtime_token,
    )

    proxy_connect_timeout_s = float(os.environ.get("BUDDY_A2A_PROXY_CONNECT_TIMEOUT_S", "15"))
    proxy_write_timeout_s = float(os.environ.get("BUDDY_A2A_PROXY_WRITE_TIMEOUT_S", "120"))
    proxy_pool_timeout_s = float(os.environ.get("BUDDY_A2A_PROXY_POOL_TIMEOUT_S", "120"))

    app.include_router(build_sessions_router(state))
    app.include_router(build_agents_router(state))
    app.include_router(build_runtime_router(state))
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
        if local_environment_manager is not None:
            await run_in_threadpool(local_environment_manager.start)

        if managed_agent_manager is not None:
            await run_in_threadpool(managed_agent_manager.reconcile_from_docker)

        if managed_agent_manager is not None and _bool_env("BUDDY_DEFAULT_MANAGED_AGENT_ENABLED", True):
            default_agent_id = os.environ.get("BUDDY_DEFAULT_MANAGED_AGENT_ID", "buddy")
            existing = await run_in_threadpool(managed_agent_manager.get_agent, default_agent_id)
            if existing is None:
                await run_in_threadpool(
                    managed_agent_manager.create_agent,
                    agent_id=default_agent_id,
                    image=os.environ.get("BUDDY_DEFAULT_MANAGED_AGENT_IMAGE", "buddy-agent-runtime:latest"),
                    config_yaml=_default_managed_agent_yaml(),
                    container_port=_int_env("BUDDY_DEFAULT_MANAGED_AGENT_PORT", 10001),
                    config_mount_path="/etc/buddy/agent.yaml",
                    extra_env={},
                    command=None,
                )
            else:
                await run_in_threadpool(managed_agent_manager.start_agent, default_agent_id)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        if managed_agent_manager is not None:
            records = await run_in_threadpool(managed_agent_manager.list_agents)
            for record in records:
                if record.container_id and record.status == "running":
                    try:
                        await run_in_threadpool(managed_agent_manager.stop_agent, record.agent_id)
                    except Exception as error:
                        print(f"Failed to stop managed agent '{record.agent_id}' during shutdown: {error}")
        if local_environment_manager is not None:
            await run_in_threadpool(local_environment_manager.stop)

    return app
