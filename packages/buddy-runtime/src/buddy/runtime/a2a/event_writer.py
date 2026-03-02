from uuid import uuid4

from a2a.types import TaskState

from buddy.session_store import SessionStore


class SessionEventWriter:
    def __init__(self, *, session_store: SessionStore, context_id: str, task_id: str) -> None:
        self._store = session_store
        self._context_id = context_id
        self._task_id = task_id
        self._event_index = self._store.next_event_index(context_id)

    def append_status_update(self, state: TaskState, message_text: str | None = None, final: bool = False) -> None:
        status_payload: dict[str, object] = {
            "state": state.value,
        }
        if message_text is not None:
            status_payload["message"] = {
                "kind": "message",
                "messageId": str(uuid4()),
                "role": "agent",
                "parts": [{"kind": "text", "text": message_text}],
            }

        self._append({
            "kind": "status-update",
            "contextId": self._context_id,
            "taskId": self._task_id,
            "final": final,
            "status": status_payload,
        })

    def append_artifact_text(self, *, artifact_id: str, name: str, text: str, append: bool = False) -> None:
        payload = {
            "kind": "artifact-update",
            "contextId": self._context_id,
            "taskId": self._task_id,
            "artifact": {
                "artifactId": artifact_id,
                "name": name,
                "parts": [{"kind": "text", "text": text}],
            },
        }
        if append:
            payload["append"] = True
        self._append(payload)

    def append_artifact_data(
        self, *, artifact_id: str, name: str, data: dict[str, object], append: bool = False
    ) -> None:
        payload = {
            "kind": "artifact-update",
            "contextId": self._context_id,
            "taskId": self._task_id,
            "artifact": {
                "artifactId": artifact_id,
                "name": name,
                "parts": [{"kind": "data", "data": data}],
            },
        }
        if append:
            payload["append"] = True
        self._append(payload)

    def _append(self, payload: dict[str, object]) -> None:
        self._store.append_event(self._context_id, self._event_index, payload)
        self._event_index += 1
