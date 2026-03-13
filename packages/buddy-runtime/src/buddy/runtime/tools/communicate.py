from uuid import uuid4

from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import Message, Part, Role, TaskArtifactUpdateEvent, TaskState, TaskStatusUpdateEvent, TextPart
from a2a.utils.message import get_message_text
from a2a.utils.parts import get_text_parts
from httpx import AsyncClient, Timeout


def _build_message(task: str) -> Message:
    return Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=task))],
        message_id=str(uuid4()),
        context_id=str(uuid4()),
    )


async def communicate(agent_url: str, task: str) -> str:
    """Send a task to another A2A agent and return its textual result.

    Args:
        agent_url: A2A endpoint URL for the destination agent.
        task: Task/message to send.

    Returns:
        Text response produced by the destination agent.
    """

    target_url = agent_url.strip()
    trimmed_task = task.strip()
    if not target_url:
        return "agent_url is required"
    if not trimmed_task:
        return "task is required"

    httpx_client = AsyncClient(timeout=Timeout(connect=10.0, read=None, write=120.0, pool=120.0))
    try:
        resolver = A2ACardResolver(httpx_client, target_url)
        agent_card = await resolver.get_agent_card()
        agent_card.url = target_url
        agent_card.additional_interfaces = None
        client = await ClientFactory.connect(
            agent_card,
            client_config=ClientConfig(httpx_client=httpx_client, accepted_output_modes=["text"]),
        )
    except Exception as error:
        await httpx_client.aclose()
        return f"Failed to connect to agent at '{target_url}': {error}"

    text_updates: list[str] = []
    artifact_stream_buffers: dict[str, str] = {}
    output_candidates: list[str] = []
    try:
        async for event in client.send_message(_build_message(trimmed_task)):
            if isinstance(event, Message):
                text = get_message_text(event)
                if text:
                    text_updates.append(text)
                continue

            _task, update = event
            if isinstance(update, TaskArtifactUpdateEvent):
                text_parts = get_text_parts(update.artifact.parts)
                if text_parts:
                    chunk = "".join(text_parts)
                    artifact_name = update.artifact.name or ""
                    artifact_id = update.artifact.artifact_id
                    if update.append:
                        prior = artifact_stream_buffers.get(artifact_id, "")
                        chunk = f"{prior}{chunk}"
                        artifact_stream_buffers[artifact_id] = chunk
                    elif artifact_id:
                        artifact_stream_buffers[artifact_id] = chunk

                    if artifact_name in {"output_start", "output_delta", "output_end", "full_output"}:
                        if chunk.strip():
                            output_candidates.append(chunk)

            if isinstance(update, TaskStatusUpdateEvent) and update.status.state in {
                TaskState.failed,
                TaskState.rejected,
                TaskState.canceled,
            }:
                status_message = get_message_text(update.status.message) if update.status.message else ""
                if status_message:
                    return f"Agent request failed: {status_message}"
                return f"Agent request failed with status '{update.status.state.value}'"
    except Exception as error:
        return f"Failed while communicating with '{target_url}': {error}"
    finally:
        close = getattr(client, "close", None)
        if close:
            await close()
        await httpx_client.aclose()

    if output_candidates:
        return output_candidates[-1]

    if text_updates:
        return text_updates[-1]
    return "Agent returned no textual response"
