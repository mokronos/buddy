from a2a.types import TaskState

from buddy.runtime.a2a.event_writer import SessionEventWriter
from buddy.session_store import SessionStore


def test_event_writer_persists_ordered_events(tmp_path) -> None:
    store = SessionStore(tmp_path / "sessions.db")
    writer = SessionEventWriter(session_store=store, context_id="ctx-1", task_id="task-1")

    writer.append_status_update(TaskState.working, "Working")
    writer.append_artifact_text(artifact_id="art-1", name="output_delta", text="Hello", append=True)
    writer.append_status_update(TaskState.completed, final=True)

    events = store.load_events("ctx-1")
    assert len(events) == 3
    assert events[0]["kind"] == "status-update"
    assert events[1]["kind"] == "artifact-update"
    assert events[2]["status"]["state"] == TaskState.completed.value
