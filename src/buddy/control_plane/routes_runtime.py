from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from buddy.control_plane.server_state import ServerState


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


def build_runtime_router(state: ServerState) -> APIRouter:
    router = APIRouter()

    def ensure_internal_auth(request: Request) -> None:
        if not state.internal_runtime_token:
            return
        provided = request.headers.get("x-buddy-internal-token")
        if provided != state.internal_runtime_token:
            raise HTTPException(status_code=401, detail="Unauthorized internal runtime request")

    @router.post("/internal/runtime/acquire")
    async def runtime_acquire(payload: RuntimeAcquireRequest, request: Request) -> JSONResponse:
        if state.local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        ensure_internal_auth(request)
        lease = await run_in_threadpool(state.local_environment_manager.acquire, payload.owner_id)
        return JSONResponse({"ownerId": lease.owner_id, "containerId": lease.container_id})

    @router.post("/internal/runtime/release")
    async def runtime_release(payload: RuntimeReleaseRequest, request: Request) -> JSONResponse:
        if state.local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        ensure_internal_auth(request)
        await run_in_threadpool(state.local_environment_manager.release, payload.owner_id, payload.reusable)
        return JSONResponse({"ok": True})

    @router.post("/internal/runtime/exec")
    async def runtime_exec(payload: RuntimeExecRequest, request: Request) -> JSONResponse:
        if state.local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        ensure_internal_auth(request)
        result = await run_in_threadpool(
            state.local_environment_manager.exec,
            payload.owner_id,
            payload.command,
            payload.timeout_s,
        )
        return JSONResponse({
            "exitCode": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })

    @router.post("/internal/runtime/read-file")
    async def runtime_read_file(payload: RuntimeReadFileRequest, request: Request) -> JSONResponse:
        if state.local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        ensure_internal_auth(request)
        try:
            content = await run_in_threadpool(state.local_environment_manager.read_file, payload.owner_id, payload.path)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return JSONResponse({"content": content})

    @router.post("/internal/runtime/write-file")
    async def runtime_write_file(payload: RuntimeWriteFileRequest, request: Request) -> JSONResponse:
        if state.local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        ensure_internal_auth(request)
        try:
            await run_in_threadpool(
                state.local_environment_manager.write_file,
                payload.owner_id,
                payload.path,
                payload.content,
            )
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return JSONResponse({"ok": True})

    @router.post("/internal/runtime/patch-file")
    async def runtime_patch_file(payload: RuntimePatchFileRequest, request: Request) -> JSONResponse:
        if state.local_environment_manager is None:
            raise HTTPException(status_code=404, detail="Internal runtime endpoints are disabled in runtime mode")
        ensure_internal_auth(request)
        try:
            replacements = await run_in_threadpool(
                state.local_environment_manager.patch_file,
                payload.owner_id,
                payload.path,
                payload.old_text,
                payload.new_text,
                payload.count,
            )
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return JSONResponse({"ok": True, "replacements": replacements})

    return router
