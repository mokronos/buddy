from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.concurrency import run_in_threadpool

from buddy.control_plane.server_state import ServerState
from buddy.control_plane.validation import validate_agent_id


def rewrite_card_payload(card: object, proxy_root: str, preferred_transport: str | None = None) -> object:
    if not isinstance(card, dict):
        return card
    card["url"] = proxy_root
    if preferred_transport and "preferredTransport" not in card and "preferred_transport" not in card:
        card["preferredTransport"] = preferred_transport
    return card


def _passthrough_headers(headers: httpx.Headers) -> dict[str, str]:
    excluded = {"content-length", "transfer-encoding", "connection", "content-encoding"}
    return {key: value for key, value in headers.items() if key.lower() not in excluded}


def _stream_proxy_timeout(connect_s: float, write_s: float, pool_s: float) -> httpx.Timeout:
    return httpx.Timeout(connect=connect_s, read=None, write=write_s, pool=pool_s)


def build_proxy_router(
    state: ServerState,
    *,
    connect_timeout_s: float,
    write_timeout_s: float,
    pool_timeout_s: float,
) -> APIRouter:
    router = APIRouter()

    async def proxy_to_target(request: Request, target_url: str) -> Response:
        raw_headers = dict(request.headers)
        raw_headers.pop("host", None)
        raw_headers.pop("content-length", None)
        body = await request.body()
        client = httpx.AsyncClient(timeout=_stream_proxy_timeout(connect_timeout_s, write_timeout_s, pool_timeout_s))
        upstream_request = client.build_request(
            method=request.method,
            url=target_url,
            params=request.query_params,
            headers=raw_headers,
            content=body,
        )
        upstream = await client.send(upstream_request, stream=True)

        passthrough_headers = _passthrough_headers(upstream.headers)
        content_type = upstream.headers.get("content-type", "")
        if "text/event-stream" in content_type.lower():

            async def stream_content():
                try:
                    async for chunk in upstream.aiter_bytes(chunk_size=1024):
                        if chunk:
                            yield chunk
                finally:
                    await upstream.aclose()
                    await client.aclose()

            return StreamingResponse(
                stream_content(),
                status_code=upstream.status_code,
                headers=passthrough_headers,
                media_type=content_type,
            )

        upstream_content = await upstream.aread()
        await upstream.aclose()
        await client.aclose()
        return Response(
            content=upstream_content,
            status_code=upstream.status_code,
            headers=passthrough_headers,
            media_type=content_type or None,
        )

    @router.api_route(
        "/a2a/managed/{agent_id}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    @router.api_route(
        "/a2a/managed/{agent_id}/{proxy_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def proxy_managed_agent(agent_id: str, request: Request, proxy_path: str = "") -> Response:
        manager = state.managed_agent_manager
        if manager is None:
            raise HTTPException(status_code=404, detail="Managed agents are disabled in runtime mode")

        normalized_agent_id = validate_agent_id(agent_id)
        try:
            await run_in_threadpool(manager.resolve_target, normalized_agent_id, "/")
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        mount_path = "/"
        card_path = "/.well-known/agent-card.json"
        proxy_root = f"{state.base_url}/a2a/managed/{normalized_agent_id}"
        if proxy_path == ".well-known/agent-card.json":
            try:
                upstream_card_url = await run_in_threadpool(manager.resolve_target, normalized_agent_id, card_path)
            except ValueError as error:
                raise HTTPException(status_code=404, detail=str(error)) from error
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    card_response = await client.get(upstream_card_url)
                    card_response.raise_for_status()
                    card = card_response.json()
            except httpx.HTTPError as error:
                raise HTTPException(status_code=502, detail=f"Failed to fetch managed agent card: {error}") from error

            return JSONResponse(rewrite_card_payload(card, proxy_root))

        relative_path = proxy_path.strip("/")
        upstream_path = f"{mount_path.rstrip('/')}/{relative_path}" if relative_path else mount_path

        try:
            target_url = await run_in_threadpool(manager.resolve_target, normalized_agent_id, upstream_path)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        return await proxy_to_target(request, target_url)

    @router.api_route(
        "/a2a/external/{agent_id}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    @router.api_route(
        "/a2a/external/{agent_id}/{proxy_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def proxy_external_agent(agent_id: str, request: Request, proxy_path: str = "") -> Response:
        normalized_agent_id = validate_agent_id(agent_id)
        record = await run_in_threadpool(state.external_agent_manager.get_agent, normalized_agent_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"External agent '{normalized_agent_id}' not found")

        mount_path = "/"
        card_path = "/.well-known/agent.json" if record.use_legacy_card_path else "/.well-known/agent-card.json"
        proxy_root = f"{state.base_url}/a2a/external/{normalized_agent_id}"
        if proxy_path in {".well-known/agent-card.json", ".well-known/agent.json"}:
            try:
                upstream_card_url = await run_in_threadpool(
                    state.external_agent_manager.resolve_target,
                    normalized_agent_id,
                    card_path,
                )
                async with httpx.AsyncClient(timeout=15.0) as client:
                    card_response = await client.get(upstream_card_url)
                    card_response.raise_for_status()
                    card = card_response.json()
            except httpx.HTTPError as error:
                raise HTTPException(status_code=502, detail=f"Failed to fetch external agent card: {error}") from error

            return JSONResponse(rewrite_card_payload(card, proxy_root, preferred_transport="JSONRPC"))

        if request.method == "POST" and proxy_path.strip("/") == "":
            try:
                rpc_payload = await request.json()
            except Exception:
                rpc_payload = None

            if isinstance(rpc_payload, dict):
                method_name = rpc_payload.get("method")
                params_payload = rpc_payload.get("params")
                if isinstance(method_name, str) and method_name in {"message/stream", "message/send"}:
                    if not isinstance(params_payload, dict):
                        params_payload = {}
                        rpc_payload["params"] = params_payload

                    configuration = params_payload.get("configuration")
                    if not isinstance(configuration, dict):
                        configuration = {}
                        params_payload["configuration"] = configuration

                    if "acceptedOutputModes" not in configuration:
                        configuration["acceptedOutputModes"] = ["text"]

                    target_url = await run_in_threadpool(
                        state.external_agent_manager.resolve_target,
                        normalized_agent_id,
                        mount_path,
                    )
                    client = httpx.AsyncClient(
                        timeout=_stream_proxy_timeout(connect_timeout_s, write_timeout_s, pool_timeout_s)
                    )
                    upstream_request = client.build_request(
                        "POST",
                        target_url,
                        headers={
                            "content-type": "application/json",
                            "accept": request.headers.get("accept", "application/json"),
                        },
                        json=rpc_payload,
                    )
                    upstream = await client.send(upstream_request, stream=True)

                    passthrough_headers = _passthrough_headers(upstream.headers)

                    content_type = upstream.headers.get("content-type", "")
                    if "text/event-stream" in content_type.lower():

                        async def stream_content():
                            try:
                                async for chunk in upstream.aiter_bytes(chunk_size=1024):
                                    if chunk:
                                        yield chunk
                            finally:
                                await upstream.aclose()
                                await client.aclose()

                        return StreamingResponse(
                            stream_content(),
                            status_code=upstream.status_code,
                            headers=passthrough_headers,
                            media_type=content_type,
                        )

                    upstream_content = await upstream.aread()
                    await upstream.aclose()
                    await client.aclose()
                    return Response(
                        content=upstream_content,
                        status_code=upstream.status_code,
                        headers=passthrough_headers,
                        media_type=content_type or None,
                    )

        stream_bridge_paths = {
            "message/stream",
            "message:stream",
            "v1/message/stream",
            "v1/message:stream",
        }
        if request.method == "POST" and proxy_path.strip("/") in stream_bridge_paths:
            try:
                rest_payload = await request.json()
            except Exception as error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSON body for external stream request: {error}",
                ) from error
            if not isinstance(rest_payload, dict):
                raise HTTPException(status_code=400, detail="Invalid stream request: body must be an object")

            rpc_payload = {
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "message/stream",
                "params": rest_payload,
            }

            target_url = await run_in_threadpool(
                state.external_agent_manager.resolve_target, normalized_agent_id, mount_path
            )
            client = httpx.AsyncClient(
                timeout=_stream_proxy_timeout(connect_timeout_s, write_timeout_s, pool_timeout_s)
            )
            upstream_request = client.build_request(
                "POST",
                target_url,
                headers={"content-type": "application/json", "accept": "text/event-stream"},
                json=rpc_payload,
            )
            upstream = await client.send(upstream_request, stream=True)

            passthrough_headers = _passthrough_headers(upstream.headers)

            content_type = upstream.headers.get("content-type", "")
            if "text/event-stream" not in content_type.lower():
                upstream_content = await upstream.aread()
                await upstream.aclose()
                await client.aclose()
                return Response(
                    content=upstream_content,
                    status_code=upstream.status_code,
                    headers=passthrough_headers,
                    media_type=content_type or None,
                )

            async def stream_content():
                try:
                    async for chunk in upstream.aiter_bytes(chunk_size=1024):
                        if chunk:
                            yield chunk
                finally:
                    await upstream.aclose()
                    await client.aclose()

            return StreamingResponse(
                stream_content(),
                status_code=upstream.status_code,
                headers=passthrough_headers,
                media_type=content_type,
            )

        relative_path = proxy_path.strip("/")
        upstream_path = f"{mount_path.rstrip('/')}/{relative_path}" if relative_path else mount_path
        try:
            target_url = await run_in_threadpool(
                state.external_agent_manager.resolve_target,
                normalized_agent_id,
                upstream_path,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        return await proxy_to_target(request, target_url)

    return router
