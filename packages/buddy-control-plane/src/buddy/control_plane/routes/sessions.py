from buddy.control_plane.server_state import ServerState
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool


def build_sessions_router(state: ServerState) -> APIRouter:
    router = APIRouter()

    @router.get("/sessions")
    async def list_sessions(request: Request) -> JSONResponse:
        limit_param = request.query_params.get("limit")
        limit = int(limit_param) if limit_param and limit_param.isdigit() else 20
        sessions = await run_in_threadpool(state.session_store.list_sessions, limit)
        return JSONResponse({"sessions": sessions})

    @router.get("/sessions/{session_id}")
    async def get_session(session_id: str) -> JSONResponse:
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session id")
        session = await run_in_threadpool(state.session_store.get_session, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        messages = await run_in_threadpool(state.session_store.load_chat_messages, session_id)
        events = await run_in_threadpool(state.session_store.load_events, session_id)
        return JSONResponse({
            "session": session,
            "messages": messages,
            "events": events,
        })

    return router
