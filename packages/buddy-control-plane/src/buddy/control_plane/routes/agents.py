from buddy.control_plane.server_state import ServerState
from buddy.control_plane.validation import derive_agent_id_from_name, validate_agent_id
from buddy.shared.runtime_config import (
    UserRuntimeAgentConfig,
    build_runtime_agent_config,
    dump_runtime_agent_config_yaml,
    parse_runtime_agent_config_yaml,
    to_user_runtime_agent_config,
)
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool


class ManagedAgentCreateRequest(BaseModel):
    config: UserRuntimeAgentConfig
    env: dict[str, str] = Field(default_factory=dict)
    command: list[str] | None = None


class ManagedAgentStartRequest(BaseModel):
    env: dict[str, str] = Field(default_factory=dict)
    command: list[str] | None = None


class ManagedAgentConfigUpdateRequest(BaseModel):
    config: UserRuntimeAgentConfig
    restart: bool = True


class ExternalAgentCreateRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=63)
    base_url: str
    use_legacy_card_path: bool = False


class ExternalAgentUpdateRequest(BaseModel):
    base_url: str
    use_legacy_card_path: bool = False


def build_agents_router(state: ServerState) -> APIRouter:
    router = APIRouter()

    @router.get("/agents")
    async def list_agents() -> JSONResponse:
        managed_records = await run_in_threadpool(state.managed_agent_manager.list_agents)
        managed_entries = [state.build_managed_entry(record) for record in managed_records]

        external_records = await run_in_threadpool(state.external_agent_manager.list_agents)
        external_entries = [state.build_external_entry(record.agent_id) for record in external_records]
        all_entries = [*managed_entries, *external_entries]

        default_key = all_entries[0]["key"] if all_entries else None

        return JSONResponse({
            "defaultAgentKey": default_key,
            "agents": all_entries,
            "managedAgents": managed_entries,
            "externalAgents": external_entries,
        })

    @router.get("/agents/external")
    async def list_external_agents() -> JSONResponse:
        records = await run_in_threadpool(state.external_agent_manager.list_agents)
        return JSONResponse({"agents": [record.__dict__ for record in records]})

    @router.post("/agents/external")
    async def create_external_agent(payload: ExternalAgentCreateRequest) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(payload.agent_id)
            record = await run_in_threadpool(
                state.external_agent_manager.create_agent,
                agent_id=normalized_agent_id,
                base_url=payload.base_url,
                use_legacy_card_path=payload.use_legacy_card_path,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        mount_path = f"/a2a/external/{record.agent_id}"
        card_file = "agent.json" if record.use_legacy_card_path else "agent-card.json"
        return JSONResponse(
            {
                "agent": record.__dict__,
                "proxyBaseUrl": f"{state.base_url}{mount_path}",
                "agentCardUrl": f"{state.base_url}{mount_path}/.well-known/{card_file}",
            },
            status_code=201,
        )

    @router.put("/agents/external/{agent_id}")
    async def update_external_agent(agent_id: str, payload: ExternalAgentUpdateRequest) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            record = await run_in_threadpool(
                state.external_agent_manager.update_agent,
                normalized_agent_id,
                base_url=payload.base_url,
                use_legacy_card_path=payload.use_legacy_card_path,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return JSONResponse({"agent": record.__dict__})

    @router.delete("/agents/external/{agent_id}")
    async def delete_external_agent(agent_id: str) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            await run_in_threadpool(state.external_agent_manager.delete_agent, normalized_agent_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return JSONResponse({"ok": True})

    @router.get("/agents/managed")
    async def list_managed_agents() -> JSONResponse:
        agents_payload = await run_in_threadpool(state.managed_agent_manager.list_agents)
        enriched_agents: list[dict[str, object]] = []
        for record in agents_payload:
            config_payload: dict[str, object] | None = None
            try:
                config_yaml = await run_in_threadpool(state.managed_agent_manager.get_agent_config, record.agent_id)
                config_payload = to_user_runtime_agent_config(parse_runtime_agent_config_yaml(config_yaml)).model_dump(
                    mode="json"
                )
            except ValueError:
                config_payload = None

            payload = {**record.__dict__}
            payload["config"] = config_payload
            enriched_agents.append(payload)

        return JSONResponse({"agents": enriched_agents})

    @router.get("/agents/managed/{agent_id}")
    async def get_managed_agent(agent_id: str) -> JSONResponse:
        normalized_agent_id = validate_agent_id(agent_id)
        record = await run_in_threadpool(state.managed_agent_manager.get_agent, normalized_agent_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Managed agent '{normalized_agent_id}' not found")
        return JSONResponse({"agent": record.__dict__})

    @router.get("/agents/managed/{agent_id}/config")
    async def get_managed_agent_config(agent_id: str) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            config_yaml = await run_in_threadpool(state.managed_agent_manager.get_agent_config, normalized_agent_id)
            config = to_user_runtime_agent_config(parse_runtime_agent_config_yaml(config_yaml))
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return JSONResponse({"config": config.model_dump(mode="json")})

    @router.put("/agents/managed/{agent_id}/config")
    async def update_managed_agent_config(agent_id: str, payload: ManagedAgentConfigUpdateRequest) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            runtime_config = build_runtime_agent_config(payload.config, agent_id=normalized_agent_id)
            record = await run_in_threadpool(
                state.managed_agent_manager.update_agent_config,
                normalized_agent_id,
                dump_runtime_agent_config_yaml(runtime_config),
                payload.restart,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Failed to update agent config: {error}") from error
        return JSONResponse({"agent": record.__dict__})

    @router.get("/agents/managed/{agent_id}/logs")
    async def get_managed_agent_logs(agent_id: str, tail: int = 200) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            record, logs = await run_in_threadpool(
                state.managed_agent_manager.get_agent_logs, normalized_agent_id, tail
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {error}") from error

        return JSONResponse({
            "agent": record.__dict__,
            "logs": logs,
        })

    @router.post("/agents/managed")
    async def create_managed_agent(payload: ManagedAgentCreateRequest) -> JSONResponse:
        try:
            normalized_agent_id = derive_agent_id_from_name(payload.config.agent.name)
            runtime_config = build_runtime_agent_config(payload.config, agent_id=normalized_agent_id)
            record = await run_in_threadpool(
                state.managed_agent_manager.create_agent,
                agent_id=normalized_agent_id,
                config_yaml=dump_runtime_agent_config_yaml(runtime_config),
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
                "proxyBaseUrl": f"{state.base_url}{mount_path}",
                "agentCardUrl": f"{state.base_url}{mount_path}/.well-known/agent-card.json",
            },
            status_code=201,
        )

    @router.post("/agents/managed/{agent_id}/start")
    async def start_managed_agent(agent_id: str, payload: ManagedAgentStartRequest) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            record = await run_in_threadpool(
                state.managed_agent_manager.start_agent,
                normalized_agent_id,
                extra_env=payload.env,
                command=payload.command,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Failed to start agent: {error}") from error
        return JSONResponse({"agent": record.__dict__})

    @router.post("/agents/managed/{agent_id}/stop")
    async def stop_managed_agent(agent_id: str) -> JSONResponse:
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            record = await run_in_threadpool(state.managed_agent_manager.stop_agent, normalized_agent_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return JSONResponse({"agent": record.__dict__})

    @router.delete("/agents/managed/{agent_id}")
    async def delete_managed_agent(agent_id: str, request: Request) -> JSONResponse:
        remove_config = request.query_params.get("removeConfig") == "true"
        try:
            normalized_agent_id = validate_agent_id(agent_id)
            await run_in_threadpool(state.managed_agent_manager.delete_agent, normalized_agent_id, remove_config)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return JSONResponse({"ok": True})

    return router
