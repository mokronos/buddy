import os
from dataclasses import dataclass, replace
from pathlib import Path
from threading import Lock
from time import perf_counter

from buddy.control_plane.manager_support import (
    emit_operation_event,
    load_json_registry,
    save_json_registry,
    utc_now_iso,
)
from buddy.control_plane.validation import normalize_external_base_url, validate_agent_id
from buddy.data_dirs import buddy_data_dir
from buddy.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExternalAgentRecord:
    agent_id: str
    base_url: str
    use_legacy_card_path: bool
    created_at: str
    updated_at: str


class ExternalAgentManager:
    def __init__(self, registry_path: Path | None = None) -> None:
        self._registry_path = registry_path or (buddy_data_dir() / "external_agents.json")
        self._lock = Lock()
        self._records: dict[str, ExternalAgentRecord] = {}
        self._load_registry()

    def list_agents(self) -> list[ExternalAgentRecord]:
        with self._lock:
            return [self._records[key] for key in sorted(self._records.keys())]

    def get_agent(self, agent_id: str) -> ExternalAgentRecord | None:
        with self._lock:
            return self._records.get(agent_id)

    def create_agent(self, *, agent_id: str, base_url: str, use_legacy_card_path: bool = False) -> ExternalAgentRecord:
        start_time = perf_counter()
        normalized_agent_id = agent_id
        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                self._ensure_agent_absent(normalized_agent_id)

                normalized_base_url = self._normalize_base_url(base_url)
                now = self._now()
                record = ExternalAgentRecord(
                    agent_id=normalized_agent_id,
                    base_url=normalized_base_url,
                    use_legacy_card_path=use_legacy_card_path,
                    created_at=now,
                    updated_at=now,
                )
                self._records[normalized_agent_id] = record
                self._save_registry()
        except Exception as error:
            self._emit_operation_event(
                "external_agent_create_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=normalized_agent_id,
                base_url=base_url,
                use_legacy_card_path=use_legacy_card_path,
            )
            raise

        self._emit_operation_event(
            "external_agent_create_completed",
            start_time=start_time,
            outcome="success",
            **self._record_log_fields(record),
        )
        return record

    def update_agent(
        self,
        agent_id: str,
        *,
        base_url: str,
        use_legacy_card_path: bool,
    ) -> ExternalAgentRecord:
        start_time = perf_counter()
        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                record = self._require_record(normalized_agent_id)
                updated = replace(
                    record,
                    base_url=self._normalize_base_url(base_url),
                    use_legacy_card_path=use_legacy_card_path,
                    updated_at=self._now(),
                )
                self._records[normalized_agent_id] = updated
                self._save_registry()
        except Exception as error:
            self._emit_operation_event(
                "external_agent_update_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=agent_id,
                base_url=base_url,
                use_legacy_card_path=use_legacy_card_path,
            )
            raise

        self._emit_operation_event(
            "external_agent_update_completed",
            start_time=start_time,
            outcome="success",
            **self._record_log_fields(updated),
        )
        return updated

    def delete_agent(self, agent_id: str) -> None:
        start_time = perf_counter()
        record: ExternalAgentRecord | None = None
        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                record = self._records.pop(normalized_agent_id, None)
                if record is None:
                    self._raise_not_found(normalized_agent_id)
                self._save_registry()
        except Exception as error:
            self._emit_operation_event(
                "external_agent_delete_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=agent_id,
                **(self._record_log_fields(record) if record is not None else {}),
            )
            raise

        self._emit_operation_event(
            "external_agent_delete_completed",
            start_time=start_time,
            outcome="success",
            **self._record_log_fields(record),
        )

    def resolve_target(self, agent_id: str, target_path: str) -> str:
        with self._lock:
            normalized_agent_id = validate_agent_id(agent_id)
            record = self._records.get(normalized_agent_id)
            if record is None:
                raise ValueError(f"External agent '{normalized_agent_id}' not found")
        base = record.base_url.rstrip("/")
        if not target_path:
            return base
        path = target_path if target_path.startswith("/") else f"/{target_path}"
        return f"{base}{path}"

    def _load_registry(self) -> None:
        self._records = load_json_registry(self._registry_path, load_record=self._load_record)

    def _save_registry(self) -> None:
        save_json_registry(self._registry_path, self._records)

    def _ensure_agent_absent(self, agent_id: str) -> None:
        if agent_id in self._records:
            raise ValueError(f"External agent '{agent_id}' already exists")

    def _require_record(self, agent_id: str) -> ExternalAgentRecord:
        record = self._records.get(agent_id)
        if record is None:
            self._raise_not_found(agent_id)
        return record

    @staticmethod
    def _raise_not_found(agent_id: str) -> None:
        raise ValueError(f"External agent '{agent_id}' not found")

    @staticmethod
    def _load_record(agent_id: str, record_data: dict[str, object]) -> ExternalAgentRecord | None:
        try:
            return ExternalAgentRecord(
                agent_id=str(record_data.get("agent_id", agent_id)),
                base_url=str(record_data["base_url"]),
                use_legacy_card_path=bool(record_data["use_legacy_card_path"]),
                created_at=str(record_data["created_at"]),
                updated_at=str(record_data["updated_at"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _record_log_fields(record: ExternalAgentRecord) -> dict[str, object]:
        return {
            "agent_id": record.agent_id,
            "base_url": record.base_url,
            "use_legacy_card_path": record.use_legacy_card_path,
        }

    def _emit_operation_event(
        self,
        event: str,
        *,
        start_time: float,
        outcome: str,
        level: str = "info",
        error: Exception | None = None,
        **fields: object,
    ) -> None:
        emit_operation_event(
            logger,
            event,
            start_time=start_time,
            outcome=outcome,
            level=level,
            error=error,
            **fields,
        )

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        allow_private_hosts = os.environ.get("BUDDY_ALLOW_PRIVATE_EXTERNAL_URLS", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return normalize_external_base_url(base_url, allow_private_hosts=allow_private_hosts)

    @staticmethod
    def _now() -> str:
        return utc_now_iso()
