import os
from pathlib import Path

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, TaskState
from a2a.utils import new_agent_text_message, new_task
from dotenv import load_dotenv
from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallPart,
)

from buddy.a2a.utils import simple_text_part
from buddy.session_store import SessionStore

from uuid import uuid4

load_dotenv()

from devtools import pprint
import subprocess
import tempfile


def execute_ts_code(code: str):
    """
    Executes code in a temporary file and returns the output.
    Make sure to console.log everything you want to see in the output.
    """
    # 1. Create a temporary TS file
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False, mode="w") as temp:
        temp.write(code)
        temp_path = temp.name

    try:
        # 2. Run via Deno (V8) with strict sandbox flags
        # --no-prompt: Fails instead of asking for permission
        # --allow-none: Blocks all network/file/env access
        result = subprocess.run(
            ["deno", "run", "--no-prompt", temp_path],
            capture_output=True,
            text=True,
            timeout=5,  # prevent infinite loops
        )

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        return "Error: Script execution timed out."
    finally:
        # 3. Cleanup
        os.remove(temp_path)


port = os.environ.get("PORT", 10001)

session_store = SessionStore(Path(".buddy") / "sessions.db")


agent_card = AgentCard(
    name="Test Agent",
    description="Test Agent",
    url=f"http://localhost:{port}",
    capabilities=AgentCapabilities(
        streaming=True,
    ),
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[],
    version="0.0.1",
)

pprint(agent_card)


class PyAIAgentExecutor(AgentExecutor):
    def __init__(self, agent: Agent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        print("\n\n\n Recieved new task with query: ", query, "\n")
        message = context.message
        if message is None:
            raise ValueError("Request context missing message")
        context_id = context.context_id
        if context_id is None:
            raise ValueError("Request context missing context_id")
        task = context.current_task or new_task(message)

        updater = TaskUpdater(event_queue, task.id, context_id)

        msg_history = session_store.load_messages(context_id)

        session_store.append_chat_message(context_id, "user", query)

        await event_queue.enqueue_event(task)
        await updater.update_status(
            TaskState.working, message=new_agent_text_message(f"Recieved new task with query: {query}")
        )
        event_index = session_store.next_event_index(context_id)
        session_store.append_event(
            context_id,
            event_index,
            {
                "kind": "status-update",
                "contextId": context_id,
                "taskId": task.id,
                "final": False,
                "status": {
                    "state": TaskState.working.value,
                    "message": {
                        "kind": "message",
                        "messageId": str(uuid4()),
                        "role": "agent",
                        "parts": [{"kind": "text", "text": f"Recieved new task with query: {query}"}],
                    },
                },
            },
        )
        event_index += 1

        output = "Agent didn't produce any output"
        res = None
        cur_artifact_id = None
        async for event in self.agent.run_stream_events(query, message_history=msg_history):
            pprint(event)

            if isinstance(event, PartStartEvent):
                part = event.part
                cur_artifact_id = str(uuid4())
                if isinstance(part, TextPart):
                    await updater.add_artifact(
                        [simple_text_part(part.content)],
                        name="output_start",
                        artifact_id=cur_artifact_id,
                    )
                    session_store.append_event(
                        context_id,
                        event_index,
                        {
                            "kind": "artifact-update",
                            "contextId": context_id,
                            "taskId": task.id,
                            "artifact": {
                                "artifactId": cur_artifact_id,
                                "name": "output_start",
                                "parts": [{"kind": "text", "text": part.content}],
                            },
                        },
                    )
                    event_index += 1
            if isinstance(event, PartDeltaEvent):
                delta = event.delta

                if isinstance(delta, TextPartDelta):
                    await updater.add_artifact(
                        [simple_text_part(delta.content_delta)],
                        name="output_delta",
                        append=True,
                        artifact_id=cur_artifact_id,
                    )
                    session_store.append_event(
                        context_id,
                        event_index,
                        {
                            "kind": "artifact-update",
                            "contextId": context_id,
                            "taskId": task.id,
                            "append": True,
                            "artifact": {
                                "artifactId": cur_artifact_id,
                                "name": "output_delta",
                                "parts": [{"kind": "text", "text": delta.content_delta}],
                            },
                        },
                    )
                    event_index += 1

            # end just repeats the whole part (probably should still send, for easier handling on client, but different artifact)
            if isinstance(event, PartEndEvent):
                part = event.part
                if isinstance(part, TextPart):
                    await updater.add_artifact(
                        [simple_text_part(part.content)],
                        name="output_end",
                        artifact_id=cur_artifact_id,
                    )
                    session_store.append_event(
                        context_id,
                        event_index,
                        {
                            "kind": "artifact-update",
                            "contextId": context_id,
                            "taskId": task.id,
                            "artifact": {
                                "artifactId": cur_artifact_id,
                                "name": "output_end",
                                "parts": [{"kind": "text", "text": part.content}],
                            },
                        },
                    )
                    event_index += 1
                if isinstance(part, ToolCallPart):
                    await updater.update_status(
                        TaskState.working,
                        message=new_agent_text_message(f"Calling tool: {part.tool_name} with args: {part.args}"),
                    )
                    session_store.append_event(
                        context_id,
                        event_index,
                        {
                            "kind": "status-update",
                            "contextId": context_id,
                            "taskId": task.id,
                            "final": False,
                            "status": {
                                "state": TaskState.working.value,
                                "message": {
                                    "kind": "message",
                                    "messageId": str(uuid4()),
                                    "role": "agent",
                                    "parts": [
                                        {
                                            "kind": "text",
                                            "text": f"Calling tool: {part.tool_name} with args: {part.args}",
                                        }
                                    ],
                                },
                            },
                        },
                    )
                    event_index += 1

            if isinstance(event, FunctionToolResultEvent):
                res = event.result

                text = f"Tool {res.tool_name} returned: {res.content}"

                await updater.add_artifact(
                    [simple_text_part(text)],
                    name="tool_result",
                    artifact_id=cur_artifact_id,
                )
                session_store.append_event(
                    context_id,
                    event_index,
                    {
                        "kind": "artifact-update",
                        "contextId": context_id,
                        "taskId": task.id,
                        "artifact": {
                            "artifactId": cur_artifact_id,
                            "name": "tool_result",
                            "parts": [{"kind": "text", "text": text}],
                        },
                    },
                )
                event_index += 1
                await updater.update_status(TaskState.working, message=new_agent_text_message("Agent thinking ..."))
                session_store.append_event(
                    context_id,
                    event_index,
                    {
                        "kind": "status-update",
                        "contextId": context_id,
                        "taskId": task.id,
                        "final": False,
                        "status": {
                            "state": TaskState.working.value,
                            "message": {
                                "kind": "message",
                                "messageId": str(uuid4()),
                                "role": "agent",
                                "parts": [{"kind": "text", "text": "Agent thinking ..."}],
                            },
                        },
                    },
                )
                event_index += 1

            if isinstance(event, AgentRunResultEvent):
                res = event.result

        if res is None:
            raise ValueError("Agent produced no result")

        res_output = getattr(res, "output", None)
        if res_output is not None:
            output = res_output

        all_messages = getattr(res, "all_messages", None)
        msgs = all_messages() if callable(all_messages) else []
        msgs_list = list(msgs) if isinstance(msgs, list) else []

        session_store.save_messages(context_id, msgs_list)

        session_store.append_event(
            context_id,
            event_index,
            {
                "kind": "artifact-update",
                "contextId": context_id,
                "taskId": task.id,
                "artifact": {
                    "artifactId": str(uuid4()),
                    "name": "full_output",
                    "parts": [{"kind": "text", "text": output}],
                },
            },
        )
        event_index += 1

        await updater.add_artifact(
            [simple_text_part(output)],
            name="full_output",
        )

        session_store.append_chat_message(context_id, "assistant", output)

        await updater.update_status(TaskState.completed)
        session_store.append_event(
            context_id,
            event_index,
            {
                "kind": "status-update",
                "contextId": context_id,
                "taskId": task.id,
                "final": True,
                "status": {
                    "state": TaskState.completed.value,
                },
            },
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancellation is not supported yet")


def create_app(agent: Agent):
    request_handler = DefaultRequestHandler(
        agent_executor=PyAIAgentExecutor(
            agent=agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    a2a_app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

    app = a2a_app.build()

    @app.route("/sessions", methods=["GET"])
    async def list_sessions(request: Request) -> JSONResponse:
        limit_param = request.query_params.get("limit")
        limit = int(limit_param) if limit_param and limit_param.isdigit() else 20
        sessions = session_store.list_sessions(limit)
        return JSONResponse({"sessions": sessions})

    @app.route("/sessions/{session_id}", methods=["GET"])
    async def get_session(request: Request) -> JSONResponse:
        session_id = request.path_params.get("session_id")
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
