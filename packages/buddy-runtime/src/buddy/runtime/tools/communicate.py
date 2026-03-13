import asyncio
import logging
import os
import socket
from uuid import uuid4

from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import Message, Part, Role, TaskArtifactUpdateEvent, TaskState, TaskStatusUpdateEvent, TextPart
from a2a.utils.message import get_message_text
from a2a.utils.parts import get_text_parts
from httpx import AsyncClient, Timeout

DEFAULT_CONTROL_PLANE_URL = "http://host.docker.internal:10001"
DEFAULT_CONTROL_PLANE_FALLBACK_URL = "http://172.17.0.1:10001"
DEFAULT_SEND_TASK_GUIDANCE = "Use an A2A base URL like http://172.17.0.3:8000/a2a."

logger = logging.getLogger(__name__)


def _build_message(task: str) -> Message:
    return Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=task))],
        message_id=str(uuid4()),
        context_id=str(uuid4()),
    )


def _normalize_control_plane_url(raw_url: str) -> str:
    normalized = raw_url.strip().rstrip("/")
    if normalized.endswith("/a2a"):
        normalized = normalized[: -len("/a2a")].rstrip("/")
    return normalized


async def _is_reachable_agent_url(httpx_client: AsyncClient, agent_url: str) -> bool:
    try:
        resolver = A2ACardResolver(httpx_client, agent_url)
        await resolver.get_agent_card()
    except Exception:
        return False
    return True


def _local_ipv4() -> str | None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("1.1.1.1", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip if isinstance(ip, str) else None
    except Exception:
        return None


async def _probe_bridge_agent(base_url: str, *, timeout_s: float = 0.35) -> dict[str, str] | None:
    try:
        async with AsyncClient(
            timeout=Timeout(connect=timeout_s, read=timeout_s, write=timeout_s, pool=timeout_s)
        ) as client:
            resolver = A2ACardResolver(client, base_url)
            card = await resolver.get_agent_card()
    except Exception:
        return None

    display_name = card.name.strip() if isinstance(card.name, str) and card.name.strip() else base_url
    return {
        "name": display_name,
        "url": base_url,
    }


async def _discover_agents_on_bridge_network() -> list[dict[str, str]]:
    local_ip = _local_ipv4()
    if not local_ip:
        return []
    octets = local_ip.split(".")
    if len(octets) != 4:
        return []

    prefix = ".".join(octets[:3])
    local_host = octets[3]
    candidate_urls = [f"http://{prefix}.{index}:8000/a2a" for index in range(1, 255) if str(index) != local_host]

    semaphore = asyncio.Semaphore(48)

    async def _run_probe(url: str) -> dict[str, str] | None:
        async with semaphore:
            return await _probe_bridge_agent(url)

    discovered = await asyncio.gather(*[_run_probe(url) for url in candidate_urls])
    unique: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for item in discovered:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        name = item.get("name")
        if not isinstance(url, str) or not isinstance(name, str):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique.append({"name": name, "url": url})
    return unique


async def send_task(agent_url: str, task: str) -> str:
    """Send a task to another A2A agent and return its textual result."""

    target_url = agent_url.strip()
    trimmed_task = task.strip()
    if not target_url:
        return f"agent_url is required. {DEFAULT_SEND_TASK_GUIDANCE}"
    if not target_url.startswith(("http://", "https://")):
        return f"agent_url must start with http:// or https://. {DEFAULT_SEND_TASK_GUIDANCE}"
    if not trimmed_task:
        return "task is required. Provide a clear instruction to send to the target agent."

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
    except Exception:
        logger.exception("send_task failed to connect", extra={"agent_url": target_url})
        await httpx_client.aclose()
        return (
            "Could not reach the target agent URL. "
            "Verify the URL points to a running A2A endpoint and is reachable from this runtime container. "
            f"{DEFAULT_SEND_TASK_GUIDANCE}"
        )

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
                    return f"Target agent could not complete the task: {status_message}"
                return (
                    "Target agent could not complete the task. "
                    "Try clarifying the task wording or choose another available agent URL."
                )
    except Exception:
        logger.exception("send_task failed during task execution", extra={"agent_url": target_url})
        return (
            "The task request was sent but failed while waiting for a response. "
            "Try a shorter task, retry the same URL, or choose another available agent URL."
        )
    finally:
        close = getattr(client, "close", None)
        if close:
            await close()
        await httpx_client.aclose()

    if output_candidates:
        return output_candidates[-1]

    if text_updates:
        return text_updates[-1]
    return "The target agent returned no text output. Try asking for a plain-text answer explicitly."


async def list_available_agents() -> list[dict[str, str]]:
    """Return discoverable agents as a simple name/url list."""

    configured_url = _normalize_control_plane_url(os.environ.get("BUDDY_CONTROL_PLANE_URL", ""))
    candidates = [
        configured_url,
        DEFAULT_CONTROL_PLANE_URL,
        DEFAULT_CONTROL_PLANE_FALLBACK_URL,
        "http://localhost:10001",
    ]
    checked: set[str] = set()

    async with AsyncClient(timeout=Timeout(connect=5.0, read=10.0, write=10.0, pool=10.0)) as client:
        for candidate in candidates:
            if not candidate or candidate in checked:
                continue
            checked.add(candidate)
            endpoint = f"{candidate}/agents"
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                payload = response.json()
            except Exception:
                logger.debug("list_available_agents could not reach %s", endpoint, exc_info=True)
                continue

            raw_agents = payload.get("agents") if isinstance(payload, dict) else None
            if not isinstance(raw_agents, list):
                continue

            agents: list[dict[str, str]] = []
            seen_urls: set[str] = set()
            for item in raw_agents:
                if not isinstance(item, dict):
                    continue

                proxy_url = item.get("url") if isinstance(item.get("url"), str) else None
                internal_url = item.get("internalUrl") if isinstance(item.get("internalUrl"), str) else None
                mount_path = item.get("mountPath") if isinstance(item.get("mountPath"), str) else None
                raw_name = item.get("name") if isinstance(item.get("name"), str) else None
                name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else None
                raw_key = item.get("key")
                key: str = raw_key if isinstance(raw_key, str) else "agent"

                candidate_urls: list[str] = []
                if internal_url:
                    candidate_urls.append(internal_url)
                if proxy_url:
                    candidate_urls.append(proxy_url)
                if mount_path:
                    candidate_urls.append(f"{candidate}{mount_path}")

                deduped_candidates: list[str] = []
                seen_candidates: set[str] = set()
                for agent_url in candidate_urls:
                    if agent_url in seen_candidates:
                        continue
                    seen_candidates.add(agent_url)
                    deduped_candidates.append(agent_url)

                selected_url: str | None = None
                for agent_url in deduped_candidates:
                    if await _is_reachable_agent_url(client, agent_url):
                        selected_url = agent_url
                        break
                if selected_url is None and deduped_candidates:
                    selected_url = deduped_candidates[0]
                if selected_url is None or selected_url in seen_urls:
                    continue

                seen_urls.add(selected_url)
                display_name: str = name or key
                agents.append({"name": display_name, "url": selected_url})

            if agents:
                return agents

    return await _discover_agents_on_bridge_network()
