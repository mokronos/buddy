import os
from dataclasses import dataclass, replace
from pathlib import Path
from threading import Lock
from time import perf_counter, sleep
from urllib.parse import urlparse

import docker
import requests
from buddy.control_plane.manager_support import (
    emit_operation_event,
    load_json_registry,
    save_json_registry,
    utc_now_iso,
)
from buddy.control_plane.validation import validate_agent_id
from buddy.data_dirs import buddy_data_dir
from buddy.shared.logging import get_logger
from buddy.shared.runtime_config import (
    load_runtime_agent_config,
    parse_runtime_agent_config_yaml,
    runtime_agent_card_path,
)
from docker.errors import NotFound

logger = get_logger(__name__)


@dataclass
class ManagedAgentRecord:
    agent_id: str
    image: str
    config_path: str
    config_mount_path: str
    container_port: int
    a2a_mount_path: str
    container_id: str | None
    host_port: int | None
    status: str
    last_error: str | None
    created_at: str
    updated_at: str


class ManagedAgentManager:
    def __init__(self, registry_path: Path | None = None) -> None:
        self._docker = docker.from_env()
        self._lock = Lock()
        self._records: dict[str, ManagedAgentRecord] = {}
        self._registry_path = registry_path or (buddy_data_dir() / "managed_agents.json")
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_registry()

    def list_agents(self) -> list[ManagedAgentRecord]:
        with self._lock:
            records = [self._refresh_status(record) for record in self._records.values()]
            self._records = {record.agent_id: record for record in records}
            self._save_registry()
            return sorted(records, key=lambda item: item.agent_id)

    def get_agent(self, agent_id: str) -> ManagedAgentRecord | None:
        with self._lock:
            record = self._records.get(agent_id)
            if record is None:
                return None
            refreshed = self._refresh_status(record)
            self._records[agent_id] = refreshed
            self._save_registry()
            return refreshed

    def create_agent(
        self,
        *,
        agent_id: str,
        image: str,
        config_yaml: str,
        container_port: int,
        config_mount_path: str,
        extra_env: dict[str, str],
        command: list[str] | None,
    ) -> ManagedAgentRecord:
        start_time = perf_counter()
        normalized_agent_id = agent_id
        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                self._ensure_agent_absent(normalized_agent_id)

                self._validate_config(normalized_agent_id, config_yaml)
                runtime_config = parse_runtime_agent_config_yaml(config_yaml)
                config_path = self._write_config(normalized_agent_id, config_yaml)
                now = self._now()
                record = ManagedAgentRecord(
                    agent_id=normalized_agent_id,
                    image=image,
                    config_path=str(config_path),
                    config_mount_path=config_mount_path,
                    container_port=runtime_config.a2a.port,
                    a2a_mount_path=runtime_config.a2a.mount_path,
                    container_id=None,
                    host_port=None,
                    status="created",
                    last_error=None,
                    created_at=now,
                    updated_at=now,
                )
                self._records[normalized_agent_id] = record
                self._save_registry()

                try:
                    started = self._start_container(record, extra_env=extra_env, command=command)
                except Exception:
                    self._records.pop(normalized_agent_id, None)
                    self._save_registry()
                    if config_path.exists():
                        config_path.unlink()
                    raise

                self._records[normalized_agent_id] = started
                self._save_registry()
                result = started
        except Exception as error:
            self._emit_operation_event(
                "managed_agent_create_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=normalized_agent_id,
                image=image,
                container_port=container_port,
                config_mount_path=config_mount_path,
                env_keys=sorted(extra_env.keys()),
                command_length=len(command or []),
            )
            raise

        self._emit_operation_event(
            "managed_agent_create_completed",
            start_time=start_time,
            outcome="success",
            env_keys=sorted(extra_env.keys()),
            command_length=len(command or []),
            **self._record_log_fields(result),
        )
        return result

    def start_agent(
        self,
        agent_id: str,
        *,
        extra_env: dict[str, str] | None = None,
        command: list[str] | None = None,
    ) -> ManagedAgentRecord:
        start_time = perf_counter()
        normalized_agent_id = agent_id
        extra_env = extra_env or {}
        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                record = self._require_record(normalized_agent_id)

                if record.container_id:
                    try:
                        container = self._docker.containers.get(record.container_id)
                        container.reload()
                        if container.status == "running":
                            refreshed = self._refresh_status(record)
                            self._records[normalized_agent_id] = refreshed
                            self._save_registry()
                            result = refreshed
                            self._emit_operation_event(
                                "managed_agent_start_completed",
                                start_time=start_time,
                                outcome="success",
                                env_keys=sorted(extra_env.keys()),
                                command_length=len(command or []),
                                **self._record_log_fields(result),
                            )
                            return result
                    except NotFound:
                        pass

                try:
                    started = self._start_container(
                        record,
                        extra_env=extra_env,
                        command=command,
                    )
                except Exception as error:
                    failed = replace(record, status="failed", last_error=str(error), updated_at=self._now())
                    self._records[normalized_agent_id] = failed
                    self._save_registry()
                    raise

                self._records[normalized_agent_id] = started
                self._save_registry()
                result = started
        except Exception as error:
            self._emit_operation_event(
                "managed_agent_start_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=normalized_agent_id,
                env_keys=sorted(extra_env.keys()),
                command_length=len(command or []),
            )
            raise

        self._emit_operation_event(
            "managed_agent_start_completed",
            start_time=start_time,
            outcome="success",
            env_keys=sorted(extra_env.keys()),
            command_length=len(command or []),
            **self._record_log_fields(result),
        )
        return result

    def stop_agent(self, agent_id: str) -> ManagedAgentRecord:
        start_time = perf_counter()
        normalized_agent_id = agent_id
        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                record = self._require_record(normalized_agent_id)

                if record.container_id:
                    try:
                        container = self._docker.containers.get(record.container_id)
                        container.stop(timeout=10)
                    except NotFound:
                        pass

                updated = replace(record, status="stopped", last_error=None, updated_at=self._now())
                self._records[normalized_agent_id] = updated
                self._save_registry()
                result = updated
        except Exception as error:
            self._emit_operation_event(
                "managed_agent_stop_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=normalized_agent_id,
            )
            raise

        self._emit_operation_event(
            "managed_agent_stop_completed",
            start_time=start_time,
            outcome="success",
            **self._record_log_fields(result),
        )
        return result

    def delete_agent(self, agent_id: str, remove_config: bool = False) -> None:
        start_time = perf_counter()
        normalized_agent_id = agent_id
        record: ManagedAgentRecord | None = None
        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                record = self._records.pop(normalized_agent_id, None)
                if record is None:
                    self._raise_missing_agent(normalized_agent_id)
                self._save_registry()

            if record.container_id:
                try:
                    container = self._docker.containers.get(record.container_id)
                    container.remove(force=True)
                except NotFound:
                    pass

            if remove_config:
                config_path = Path(record.config_path)
                if config_path.exists():
                    config_path.unlink()
        except Exception as error:
            self._emit_operation_event(
                "managed_agent_delete_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=normalized_agent_id,
                remove_config=remove_config,
                **(self._record_log_fields(record) if record is not None else {}),
            )
            raise

        self._emit_operation_event(
            "managed_agent_delete_completed",
            start_time=start_time,
            outcome="success",
            remove_config=remove_config,
            **self._record_log_fields(record),
        )

    def get_agent_config(self, agent_id: str) -> str:
        with self._lock:
            agent_id = validate_agent_id(agent_id)
            record = self._records.get(agent_id)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")
            config_path = Path(record.config_path)
            if not config_path.exists():
                raise ValueError(f"Config file for agent '{agent_id}' does not exist")
            return config_path.read_text(encoding="utf-8")

    def update_agent_config(self, agent_id: str, config_yaml: str, restart: bool = True) -> ManagedAgentRecord:
        start_time = perf_counter()
        normalized_agent_id = agent_id
        try:
            runtime_config = parse_runtime_agent_config_yaml(config_yaml)
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                record = self._require_record(normalized_agent_id)
                self._validate_config(normalized_agent_id, config_yaml)
                Path(record.config_path).write_text(config_yaml, encoding="utf-8")
                updated_fields: dict[str, object] = {}
                if record.status != "running" or restart:
                    updated_fields = {
                        "container_port": runtime_config.a2a.port,
                        "a2a_mount_path": runtime_config.a2a.mount_path,
                    }
                updated = replace(record, **updated_fields, updated_at=self._now())
                self._records[normalized_agent_id] = updated
                self._save_registry()

            if restart and updated.status == "running":
                self.stop_agent(normalized_agent_id)
                result = self.start_agent(normalized_agent_id)
            else:
                result = updated
        except Exception as error:
            self._emit_operation_event(
                "managed_agent_update_config_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=normalized_agent_id,
                restart=restart,
                config_size_bytes=len(config_yaml.encode("utf-8")),
            )
            raise

        self._emit_operation_event(
            "managed_agent_update_config_completed",
            start_time=start_time,
            outcome="success",
            restart=restart,
            config_size_bytes=len(config_yaml.encode("utf-8")),
            **self._record_log_fields(result),
        )
        return result

    def resolve_target(self, agent_id: str, path: str) -> str:
        agent_id = validate_agent_id(agent_id)
        record = self.get_agent(agent_id)
        if record is None:
            raise ValueError(f"Agent '{agent_id}' does not exist")
        if record.status != "running" or record.host_port is None:
            raise ValueError(f"Agent '{agent_id}' is not running")
        suffix = path if path.startswith("/") else f"/{path}"
        return f"http://127.0.0.1:{record.host_port}{suffix}"

    def get_agent_logs(self, agent_id: str, tail: int = 200) -> tuple[ManagedAgentRecord, str]:
        start_time = perf_counter()
        if tail <= 0:
            raise ValueError("tail must be greater than 0")

        try:
            with self._lock:
                normalized_agent_id = validate_agent_id(agent_id)
                record = self._require_record(normalized_agent_id)

                refreshed = self._refresh_status(record)
                self._records[normalized_agent_id] = refreshed
                self._save_registry()

            if not refreshed.container_id:
                logs = ""
                result = refreshed
            else:
                try:
                    container = self._docker.containers.get(refreshed.container_id)
                    logs = container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
                    result = refreshed
                except NotFound:
                    missing = replace(
                        refreshed,
                        container_id=None,
                        host_port=None,
                        status="missing",
                        updated_at=self._now(),
                    )
                    with self._lock:
                        self._records[normalized_agent_id] = missing
                        self._save_registry()
                    logs = ""
                    result = missing
        except Exception as error:
            self._emit_operation_event(
                "managed_agent_get_logs_completed",
                start_time=start_time,
                level="error",
                outcome="error",
                error=error,
                agent_id=agent_id,
                tail=tail,
            )
            raise

        self._emit_operation_event(
            "managed_agent_get_logs_completed",
            start_time=start_time,
            outcome="success",
            tail=tail,
            log_size_bytes=len(logs.encode("utf-8")),
            **self._record_log_fields(result),
        )
        return result, logs

    def _start_container(
        self,
        record: ManagedAgentRecord,
        *,
        extra_env: dict[str, str],
        command: list[str] | None,
    ) -> ManagedAgentRecord:
        runtime_config = self._load_runtime_config(record.config_path)
        inherited_env = {
            key: value
            for key in [
                "OPENROUTER_API_KEY",
                "OPENAI_API_KEY",
                "LANGFUSE_PUBLIC_KEY",
                "LANGFUSE_SECRET_KEY",
                "LANGFUSE_HOST",
                "LANGFUSE_BASE_URL",
            ]
            if (value := os.environ.get(key))
        }
        env = {
            "BUDDY_AGENT_CONFIG": record.config_mount_path,
            **inherited_env,
            **extra_env,
        }
        if "LANGFUSE_HOST" not in env and env.get("LANGFUSE_PUBLIC_KEY") and env.get("LANGFUSE_SECRET_KEY"):
            env["LANGFUSE_HOST"] = os.environ.get("BUDDY_LANGFUSE_HOST", "http://host.docker.internal:3000")
        if "LANGFUSE_BASE_URL" not in env and isinstance(env.get("LANGFUSE_HOST"), str):
            env["LANGFUSE_BASE_URL"] = env["LANGFUSE_HOST"]
        for key in ("LANGFUSE_HOST", "LANGFUSE_BASE_URL"):
            raw_value = env.get(key)
            if not isinstance(raw_value, str):
                continue
            parsed = urlparse(raw_value)
            if parsed.hostname not in {"localhost", "127.0.0.1"}:
                continue
            port_part = f":{parsed.port}" if parsed.port else ""
            path_part = parsed.path or ""
            env[key] = f"{parsed.scheme}://host.docker.internal{port_part}{path_part}"

        self._prune_stale_agent_containers(record.agent_id)

        port_key = f"{runtime_config.a2a.port}/tcp"
        container_name = self._agent_container_name(record.agent_id)
        created_container = False
        container = None
        try:
            container = self._docker.containers.get(container_name)
            container.reload()
            if container.status != "running":
                container.remove(force=True)
        except NotFound:
            container = None

        if container is None or container.status != "running":
            container = self._docker.containers.run(
                record.image,
                detach=True,
                name=container_name,
                command=command,
                environment=env,
                ports={port_key: ("127.0.0.1", 0)},
                extra_hosts={"host.docker.internal": "host-gateway"},
                volumes={record.config_path: {"bind": record.config_mount_path, "mode": "ro"}},
                labels={
                    "buddy.managed_agent": "true",
                    "buddy.agent_id": record.agent_id,
                    "buddy.config_path": record.config_path,
                    "buddy.config_mount_path": record.config_mount_path,
                    "buddy.container_port": str(runtime_config.a2a.port),
                    "buddy.a2a_mount_path": runtime_config.a2a.mount_path,
                },
            )
            created_container = True

        container.reload()
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        bindings = ports.get(port_key)
        if not bindings:
            if created_container:
                container.remove(force=True)
            raise RuntimeError(f"Container for '{record.agent_id}' did not expose port {runtime_config.a2a.port}")
        host_port = int(bindings[0]["HostPort"])

        try:
            self._wait_for_a2a_ready(record.agent_id, host_port, runtime_config.a2a.mount_path)
        except Exception as error:
            if created_container:
                container.remove(force=True)
            raise RuntimeError(f"Managed agent '{record.agent_id}' failed to become ready: {error}") from error

        return replace(
            record,
            container_port=runtime_config.a2a.port,
            a2a_mount_path=runtime_config.a2a.mount_path,
            container_id=container.id,
            host_port=host_port,
            status=container.status,
            last_error=None,
            updated_at=self._now(),
        )

    def _refresh_status(self, record: ManagedAgentRecord) -> ManagedAgentRecord:
        if not record.container_id:
            return record
        try:
            container = self._docker.containers.get(record.container_id)
            container.reload()
        except NotFound:
            return replace(
                record,
                container_id=None,
                host_port=None,
                status="missing",
                last_error=None,
                updated_at=self._now(),
            )

        status = container.status
        if status != "running":
            return replace(record, status=status, last_error=None, updated_at=self._now())

        port_key = f"{record.container_port}/tcp"
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        bindings = ports.get(port_key)
        host_port = int(bindings[0]["HostPort"]) if bindings else None
        return replace(record, host_port=host_port, status=status, last_error=None, updated_at=self._now())

    def _write_config(self, agent_id: str, config_yaml: str) -> Path:
        config_dir = buddy_data_dir() / "agents" / agent_id
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "agent.yaml"
        config_path.write_text(config_yaml, encoding="utf-8")
        return config_path

    def _load_registry(self) -> None:
        self._records = load_json_registry(self._registry_path, load_record=self._load_record)

    def reconcile_from_docker(self) -> list[ManagedAgentRecord]:
        start_time = perf_counter()
        discovered = self._docker.containers.list(all=True, filters={"label": "buddy.managed_agent=true"})
        with self._lock:
            for container in discovered:
                container.reload()
                labels = container.labels or {}
                labeled_agent_id = labels.get("buddy.agent_id")
                if not isinstance(labeled_agent_id, str):
                    continue
                try:
                    agent_id = validate_agent_id(labeled_agent_id)
                except ValueError:
                    continue

                existing = self._records.get(agent_id)
                if existing is None:
                    config_path = labels.get("buddy.config_path")
                    config_mount_path = labels.get("buddy.config_mount_path")
                    container_port_raw = labels.get("buddy.container_port")
                    a2a_mount_path = labels.get("buddy.a2a_mount_path")
                    if not isinstance(config_path, str) or not isinstance(config_mount_path, str):
                        continue
                    try:
                        container_port = int(container_port_raw) if isinstance(container_port_raw, str) else 10001
                    except ValueError:
                        container_port = 10001
                    if not isinstance(a2a_mount_path, str):
                        a2a_mount_path = "/"
                    now = self._now()
                    image_obj = container.image
                    tags = image_obj.tags if image_obj is not None else []
                    existing = ManagedAgentRecord(
                        agent_id=agent_id,
                        image=tags[0] if tags else "unknown",
                        config_path=config_path,
                        config_mount_path=config_mount_path,
                        container_port=container_port,
                        a2a_mount_path=a2a_mount_path,
                        container_id=container.id,
                        host_port=None,
                        status=container.status,
                        last_error=None,
                        created_at=now,
                        updated_at=now,
                    )

                refreshed = self._refresh_status(existing)
                if refreshed.container_id is None:
                    refreshed = replace(refreshed, container_id=container.id, status=container.status, updated_at=self._now())
                    refreshed = self._refresh_status(refreshed)

                self._records[agent_id] = refreshed

            self._save_registry()
            result = sorted(self._records.values(), key=lambda item: item.agent_id)

        self._emit_operation_event(
            "managed_agent_reconcile_completed",
            start_time=start_time,
            outcome="success",
            discovered_count=len(discovered),
            managed_agent_count=len(result),
        )
        return result

    def _validate_config(self, agent_id: str, config_yaml: str) -> None:
        try:
            config = parse_runtime_agent_config_yaml(config_yaml)
        except (TypeError, ValueError) as error:
            raise ValueError(str(error)) from error
        if config.agent.id != agent_id:
            raise ValueError(f"Config agent.id ('{config.agent.id}') must match managed agent id ('{agent_id}')")

    def _wait_for_a2a_ready(self, agent_id: str, host_port: int, mount_path: str) -> None:
        base_url = f"http://127.0.0.1:{host_port}"
        agent_card_url = f"{base_url}{runtime_agent_card_path(mount_path)}"
        delay = 0.2
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                card_response = requests.get(agent_card_url, timeout=2)
                if card_response.ok:
                    payload = card_response.json()
                    if isinstance(payload, dict) and isinstance(payload.get("name"), str):
                        return
            except requests.RequestException:
                pass
            sleep(delay)
            delay = min(delay * 2, 2.0)
        raise RuntimeError(f"Managed agent '{agent_id}' failed readiness check at {agent_card_url}")

    def _save_registry(self) -> None:
        save_json_registry(self._registry_path, self._records)

    def _ensure_agent_absent(self, agent_id: str) -> None:
        if agent_id in self._records:
            raise ValueError(f"Agent '{agent_id}' already exists")

    def _require_record(self, agent_id: str) -> ManagedAgentRecord:
        record = self._records.get(agent_id)
        if record is None:
            self._raise_missing_agent(agent_id)
        return record

    @staticmethod
    def _raise_missing_agent(agent_id: str) -> None:
        raise ValueError(f"Agent '{agent_id}' does not exist")

    @staticmethod
    def _load_record(_agent_id: str, record_data: dict[str, object]) -> ManagedAgentRecord | None:
        try:
            return ManagedAgentRecord(**record_data)
        except TypeError:
            return None

    @staticmethod
    def _record_log_fields(record: ManagedAgentRecord) -> dict[str, object]:
        return {
            "agent_id": record.agent_id,
            "image": record.image,
            "container_port": record.container_port,
            "a2a_mount_path": record.a2a_mount_path,
            "container_id": record.container_id,
            "host_port": record.host_port,
            "status": record.status,
            "config_mount_path": record.config_mount_path,
        }

    @staticmethod
    def _load_runtime_config(config_path: str):
        return load_runtime_agent_config(Path(config_path))

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

    def _agent_container_name(self, agent_id: str) -> str:
        return f"buddy-agent-{self._slug(agent_id)}"

    def _prune_stale_agent_containers(self, agent_id: str) -> None:
        canonical_name = self._agent_container_name(agent_id)
        managed_containers = self._docker.containers.list(
            all=True,
            filters={"label": ["buddy.managed_agent=true", f"buddy.agent_id={agent_id}"]},
        )
        for container in managed_containers:
            container.reload()
            if container.name == canonical_name:
                continue
            if container.status == "running":
                continue
            container.remove(force=True)

    @staticmethod
    def _slug(value: str) -> str:
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
        return slug or "agent"

    @staticmethod
    def _now() -> str:
        return utc_now_iso()
