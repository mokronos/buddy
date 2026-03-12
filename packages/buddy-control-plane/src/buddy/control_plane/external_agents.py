import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from buddy.control_plane.validation import normalize_external_base_url, validate_agent_id
from buddy.data_dirs import buddy_data_dir
from buddy.shared.logging import emit_event, get_logger

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
        self._records: dict[str, ExternalAgentRecord] = {}
        self._load_registry()

    def list_agents(self) -> list[ExternalAgentRecord]:
        return [self._records[key] for key in sorted(self._records.keys())]

    def get_agent(self, agent_id: str) -> ExternalAgentRecord | None:
        return self._records.get(agent_id)

    def create_agent(self, *, agent_id: str, base_url: str, use_legacy_card_path: bool = False) -> ExternalAgentRecord:
        start_time = perf_counter()
        normalized_agent_id = agent_id
        try:
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
            record = self._require_record(agent_id)

            updated = ExternalAgentRecord(
                agent_id=record.agent_id,
                base_url=self._normalize_base_url(base_url),
                use_legacy_card_path=use_legacy_card_path,
                created_at=record.created_at,
                updated_at=self._now(),
            )
            self._records[agent_id] = updated
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
            record = self._records.pop(agent_id, None)
            if record is None:
                self._raise_not_found(agent_id)
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
        record = self._records.get(agent_id)
        if record is None:
            raise ValueError(f"External agent '{agent_id}' not found")
        base = record.base_url.rstrip("/")
        if not target_path:
            return base
        path = target_path if target_path.startswith("/") else f"/{target_path}"
        return f"{base}{path}"

    def _load_registry(self) -> None:
        if not self._registry_path.exists():
            self._records = {}
            return

        raw = self._registry_path.read_text(encoding="utf-8")
        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            self._records = {}
            return

        loaded: dict[str, ExternalAgentRecord] = {}
        for agent_id, record_data in data.items():
            if not isinstance(record_data, dict):
                continue
            try:
                loaded[agent_id] = ExternalAgentRecord(
                    agent_id=str(record_data.get("agent_id", agent_id)),
                    base_url=str(record_data["base_url"]),
                    use_legacy_card_path=bool(record_data["use_legacy_card_path"]),
                    created_at=str(record_data["created_at"]),
                    updated_at=str(record_data["updated_at"]),
                )
            except (KeyError, TypeError, ValueError):
                continue
        self._records = loaded

    def _save_registry(self) -> None:
        payload = {agent_id: asdict(record) for agent_id, record in self._records.items()}
        self._registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

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
        return datetime.now(tz=UTC).isoformat()
