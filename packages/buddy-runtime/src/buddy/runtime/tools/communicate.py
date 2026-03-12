from uuid import uuid4

from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import Message, Part, Role, TaskState, TaskStatusUpdateEvent, TextPart
from a2a.utils.message import get_message_text


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

    try:
        client = await ClientFactory.connect(target_url, client_config=ClientConfig())
    except Exception as error:
        return f"Failed to connect to agent at '{target_url}': {error}"

    text_updates: list[str] = []
    try:
        async for event in client.send_message(_build_message(trimmed_task)):
            if isinstance(event, Message):
                text = get_message_text(event)
                if text:
                    text_updates.append(text)
                continue

            _task, update = event
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

    if text_updates:
        return text_updates[-1]
    return "Agent returned no textual response"
