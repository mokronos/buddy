from __future__ import annotations

import asyncio
import sys
import uuid
from typing import Any, Optional

import typer
from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import (
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils.message import get_message_text
from a2a.utils.parts import get_text_parts

app = typer.Typer(no_args_is_help=True)


def _build_message(text: str, context_id: str, task_id: str | None = None) -> Message:
    return Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
        message_id=str(uuid.uuid4()),
        context_id=context_id,
        task_id=task_id,
    )


def _render_message(message: Message) -> None:
    text = get_message_text(message)
    if text:
        typer.echo(text)


def _render_status(update: TaskStatusUpdateEvent) -> None:
    status = update.status
    text = get_message_text(status.message) if status.message else ""
    if text:
        typer.echo(f"[status] {text}")
    else:
        typer.echo(f"[status] {status.state.value}")


def _render_artifact(update: TaskArtifactUpdateEvent) -> bool:
    parts = get_text_parts(update.artifact.parts)
    if not parts:
        return False
    content = "".join(parts)
    if update.append:
        sys.stdout.write(content)
        sys.stdout.flush()
        return True
    typer.echo(content)
    return False


def _is_final_status(update: TaskStatusUpdateEvent) -> bool:
    return update.final or update.status.state in {
        TaskState.completed,
        TaskState.failed,
        TaskState.canceled,
        TaskState.rejected,
    }


async def _stream_message(client: Any, context_id: str, text: str) -> None:
    appended_output = False
    streamed_output = False
    final_output_rendered = False
    message = _build_message(text, context_id)
    async for event in client.send_message(message):
        if isinstance(event, Message):
            _render_message(event)
            continue
        task, update = event
        if update is None:
            if task.status:
                typer.echo(f"[status] {task.status.state.value}")
            continue
        if isinstance(update, TaskStatusUpdateEvent):
            _render_status(update)
            if appended_output and _is_final_status(update):
                typer.echo("")
                appended_output = False
            continue
        if isinstance(update, TaskArtifactUpdateEvent):
            artifact_name = update.artifact.name or ""
            if artifact_name == "output_start":
                continue
            if artifact_name == "output_delta":
                streamed_output = True
                appended_output = _render_artifact(update) or appended_output
                if update.last_chunk and appended_output:
                    typer.echo("")
                    appended_output = False
                continue
            if artifact_name in {"output_end", "full_output"}:
                if streamed_output or final_output_rendered:
                    continue
                _render_artifact(update)
                final_output_rendered = True
                continue
            _render_artifact(update)


async def _chat_loop(url: str, session_id: str) -> None:
    typer.echo(f"Session: {session_id}")
    typer.echo("Type :exit to quit.")
    client: Any = await ClientFactory.connect(url, client_config=ClientConfig())
    try:
        while True:
            try:
                user_input = input("you: ")
            except (EOFError, KeyboardInterrupt):
                typer.echo("")
                break
            if not user_input.strip():
                continue
            if user_input.strip() in {":exit", ":quit"}:
                break
            await _stream_message(client, session_id, user_input)
    finally:
        close = getattr(client, "close", None)
        if close:
            await close()


@app.command()
def server(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server."),
    port: int = typer.Option(10001, help="Port to bind the server."),
    reload: bool = typer.Option(False, help="Enable auto-reload."),
) -> None:
    import uvicorn

    from buddy.main import app as buddy_app

    uvicorn.run(buddy_app, host=host, port=port, reload=reload)


@app.command()
def chat(
    url: str = typer.Option("http://localhost:10001/a2a", help="A2A server base URL."),
    session: Optional[str] = typer.Option(None, help="Session/context ID."),
) -> None:
    session_id = session or str(uuid.uuid4())
    try:
        asyncio.run(_chat_loop(url, session_id))
    except KeyboardInterrupt:
        typer.echo("")
