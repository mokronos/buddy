import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from time import sleep

import docker
import requests
from docker.errors import NotFound

from buddy.data_dirs import buddy_data_dir


@dataclass
class ManagedAgentRecord:
    agent_id: str
    image: str
    config_path: str
    config_mount_path: str
    container_port: int
    container_id: str | None
    host_port: int | None
    status: str
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
        with self._lock:
            if agent_id in self._records:
                raise ValueError(f"Agent '{agent_id}' already exists")

            config_path = self._write_config(agent_id, config_yaml)
            now = self._now()
            record = ManagedAgentRecord(
                agent_id=agent_id,
                image=image,
                config_path=str(config_path),
                config_mount_path=config_mount_path,
                container_port=container_port,
                container_id=None,
                host_port=None,
                status="created",
                created_at=now,
                updated_at=now,
            )
            self._records[agent_id] = record
            self._save_registry()

            started = self._start_container(record, extra_env=extra_env, command=command)
            self._records[agent_id] = started
            self._save_registry()
            return started

    def start_agent(
        self,
        agent_id: str,
        *,
        extra_env: dict[str, str] | None = None,
        command: list[str] | None = None,
    ) -> ManagedAgentRecord:
        with self._lock:
            record = self._records.get(agent_id)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")

            if record.container_id:
                try:
                    container = self._docker.containers.get(record.container_id)
                    container.reload()
                    if container.status == "running":
                        refreshed = self._refresh_status(record)
                        self._records[agent_id] = refreshed
                        self._save_registry()
                        return refreshed
                except NotFound:
                    pass

            started = self._start_container(
                record,
                extra_env=extra_env or {},
                command=command,
            )
            self._records[agent_id] = started
            self._save_registry()
            return started

    def stop_agent(self, agent_id: str) -> ManagedAgentRecord:
        with self._lock:
            record = self._records.get(agent_id)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")
            if not record.container_id:
                return record

            try:
                container = self._docker.containers.get(record.container_id)
                container.stop(timeout=10)
            except NotFound:
                pass

            updated = ManagedAgentRecord(**{
                **asdict(record),
                "status": "stopped",
                "updated_at": self._now(),
            })
            self._records[agent_id] = updated
            self._save_registry()
            return updated

    def delete_agent(self, agent_id: str, remove_config: bool = False) -> None:
        with self._lock:
            record = self._records.pop(agent_id, None)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")
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

    def resolve_target(self, agent_id: str, path: str) -> str:
        record = self.get_agent(agent_id)
        if record is None:
            raise ValueError(f"Agent '{agent_id}' does not exist")
        if record.status != "running" or record.host_port is None:
            raise ValueError(f"Agent '{agent_id}' is not running")
        suffix = path if path.startswith("/") else f"/{path}"
        return f"http://127.0.0.1:{record.host_port}{suffix}"

    def _start_container(
        self,
        record: ManagedAgentRecord,
        *,
        extra_env: dict[str, str],
        command: list[str] | None,
    ) -> ManagedAgentRecord:
        env = {
            "BUDDY_AGENT_CONFIG": record.config_mount_path,
            **extra_env,
        }
        port_key = f"{record.container_port}/tcp"
        container = self._docker.containers.run(
            record.image,
            detach=True,
            command=command,
            environment=env,
            ports={port_key: ("127.0.0.1", 0)},
            volumes={record.config_path: {"bind": record.config_mount_path, "mode": "ro"}},
            labels={
                "buddy.managed_agent": "true",
                "buddy.agent_id": record.agent_id,
            },
        )
        container.reload()
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        bindings = ports.get(port_key)
        if not bindings:
            container.remove(force=True)
            raise RuntimeError(f"Container for '{record.agent_id}' did not expose port {record.container_port}")
        host_port = int(bindings[0]["HostPort"])

        try:
            self._wait_for_a2a_ready(record.agent_id, host_port)
        except Exception as error:
            container.remove(force=True)
            raise RuntimeError(f"Managed agent '{record.agent_id}' failed to become ready: {error}") from error

        return ManagedAgentRecord(**{
            **asdict(record),
            "container_id": container.id,
            "host_port": host_port,
            "status": container.status,
            "updated_at": self._now(),
        })

    def _refresh_status(self, record: ManagedAgentRecord) -> ManagedAgentRecord:
        if not record.container_id:
            return record
        try:
            container = self._docker.containers.get(record.container_id)
            container.reload()
        except NotFound:
            return ManagedAgentRecord(**{
                **asdict(record),
                "container_id": None,
                "host_port": None,
                "status": "missing",
                "updated_at": self._now(),
            })

        status = container.status
        if status != "running":
            return ManagedAgentRecord(**{
                **asdict(record),
                "status": status,
                "updated_at": self._now(),
            })

        port_key = f"{record.container_port}/tcp"
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        bindings = ports.get(port_key)
        host_port = int(bindings[0]["HostPort"]) if bindings else None
        return ManagedAgentRecord(**{
            **asdict(record),
            "host_port": host_port,
            "status": status,
            "updated_at": self._now(),
        })

    def _write_config(self, agent_id: str, config_yaml: str) -> Path:
        config_dir = buddy_data_dir() / "agents" / agent_id
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "agent.yaml"
        config_path.write_text(config_yaml, encoding="utf-8")
        return config_path

    def _load_registry(self) -> None:
        if not self._registry_path.exists():
            self._records = {}
            return
        raw = self._registry_path.read_text(encoding="utf-8")
        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            self._records = {}
            return
        loaded: dict[str, ManagedAgentRecord] = {}
        for agent_id, record_data in data.items():
            if not isinstance(record_data, dict):
                continue
            try:
                loaded[agent_id] = ManagedAgentRecord(**record_data)
            except TypeError:
                continue
        self._records = loaded

    def _wait_for_a2a_ready(self, agent_id: str, host_port: int) -> None:
        url = f"http://127.0.0.1:{host_port}/.well-known/agent-card.json"
        delay = 0.2
        max_attempts = 8
        for _ in range(max_attempts):
            try:
                response = requests.get(url, timeout=2)
                if response.ok:
                    return
            except requests.RequestException:
                pass
            sleep(delay)
            delay = min(delay * 2, 2.0)
        raise RuntimeError(f"Managed agent '{agent_id}' failed readiness check at {url}")

    def _save_registry(self) -> None:
        payload = {agent_id: asdict(record) for agent_id, record in self._records.items()}
        self._registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=UTC).isoformat()
