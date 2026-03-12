import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter


def load_json_registry[RecordT](
    registry_path: Path,
    *,
    load_record: Callable[[str, dict[str, object]], RecordT | None],
) -> dict[str, RecordT]:
    if not registry_path.exists():
        return {}

    raw = registry_path.read_text(encoding="utf-8")
    data = json.loads(raw) if raw else {}
    if not isinstance(data, dict):
        return {}

    loaded: dict[str, RecordT] = {}
    for record_id, record_data in data.items():
        if not isinstance(record_data, dict):
            continue
        record = load_record(record_id, record_data)
        if record is not None:
            loaded[record_id] = record
    return loaded


def save_json_registry(registry_path: Path, records: Mapping[str, object]) -> None:
    payload = {record_id: asdict(record) for record_id, record in records.items()}
    registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def emit_operation_event(
    logger: logging.Logger,
    event: str,
    *,
    start_time: float,
    outcome: str,
    level: str = "info",
    error: Exception | None = None,
    **fields: object,
) -> None:
    from buddy.shared.logging import emit_event

    emit_event(
        logger,
        event,
        level=level,
        duration_ms=round((perf_counter() - start_time) * 1000, 3),
        outcome=outcome,
        error_type=type(error).__name__ if error is not None else None,
        error_message=str(error) if error is not None else None,
        **fields,
    )


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()
