import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from time import sleep
from urllib.parse import urlparse

import docker
import requests
from buddy.control_plane.validation import validate_agent_id
from buddy.data_dirs import buddy_data_dir
from buddy.shared.runtime_config import parse_runtime_agent_config_yaml
from docker.errors import APIError, NotFound


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
        with self._lock:
            agent_id = validate_agent_id(agent_id)
            if agent_id in self._records:
                raise ValueError(f"Agent '{agent_id}' already exists")

            self._validate_config(agent_id, config_yaml)
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
                last_error=None,
                created_at=now,
                updated_at=now,
            )
            self._records[agent_id] = record
            self._save_registry()

            try:
                started = self._start_container(record, extra_env=extra_env, command=command)
            except Exception as error:
                failed = ManagedAgentRecord(**{
                    **asdict(record),
                    "status": "failed",
                    "last_error": str(error),
                    "updated_at": self._now(),
                })
                self._records[agent_id] = failed
                self._save_registry()
                raise

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
            agent_id = validate_agent_id(agent_id)
            record = self._records.get(agent_id)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")

            if record.container_id:
                try:
                    container = self._docker.containers.get(record.container_id)
                    container.reload()
                    if container.status == "running":
                        network_name = self._agent_network_name(agent_id)
                        env_daemon_name = self._agent_env_daemon_name(agent_id)
                        expected_docker_hosts = (f"tcp://{env_daemon_name}:2375",)
                        if self._runtime_container_compatible(container, expected_docker_hosts, network_name):
                            self._ensure_agent_network(agent_id)
                            self._ensure_env_daemon_container(agent_id, network_name)
                            refreshed = self._refresh_status(record)
                            self._records[agent_id] = refreshed
                            self._save_registry()
                            return refreshed
                except NotFound:
                    pass

            try:
                started = self._start_container(
                    record,
                    extra_env=extra_env or {},
                    command=command,
                )
            except Exception as error:
                failed = ManagedAgentRecord(**{
                    **asdict(record),
                    "status": "failed",
                    "last_error": str(error),
                    "updated_at": self._now(),
                })
                self._records[agent_id] = failed
                self._save_registry()
                raise

            self._records[agent_id] = started
            self._save_registry()
            return started

    def stop_agent(self, agent_id: str) -> ManagedAgentRecord:
        with self._lock:
            agent_id = validate_agent_id(agent_id)
            record = self._records.get(agent_id)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")

            if record.container_id:
                try:
                    container = self._docker.containers.get(record.container_id)
                    container.stop(timeout=10)
                except NotFound:
                    pass

            try:
                env_daemon = self._docker.containers.get(self._agent_env_daemon_name(agent_id))
                env_daemon.stop(timeout=10)
            except NotFound:
                pass

            updated = ManagedAgentRecord(**{
                **asdict(record),
                "status": "stopped",
                "last_error": None,
                "updated_at": self._now(),
            })
            self._records[agent_id] = updated
            self._save_registry()
            return updated

    def delete_agent(self, agent_id: str, remove_config: bool = False) -> None:
        with self._lock:
            agent_id = validate_agent_id(agent_id)
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

        try:
            env_daemon = self._docker.containers.get(self._agent_env_daemon_name(agent_id))
            env_daemon.remove(force=True)
        except NotFound:
            pass

        try:
            network = self._docker.networks.get(self._agent_network_name(agent_id))
            network.remove()
        except NotFound:
            pass
        except APIError:
            pass

        if remove_config:
            config_path = Path(record.config_path)
            if config_path.exists():
                config_path.unlink()

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
        with self._lock:
            agent_id = validate_agent_id(agent_id)
            record = self._records.get(agent_id)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")
            self._validate_config(agent_id, config_yaml)
            Path(record.config_path).write_text(config_yaml, encoding="utf-8")
            updated = ManagedAgentRecord(**{
                **asdict(record),
                "updated_at": self._now(),
            })
            self._records[agent_id] = updated
            self._save_registry()

        if restart and updated.status == "running":
            self.stop_agent(agent_id)
            return self.start_agent(agent_id)
        return updated

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
        if tail <= 0:
            raise ValueError("tail must be greater than 0")

        with self._lock:
            agent_id = validate_agent_id(agent_id)
            record = self._records.get(agent_id)
            if record is None:
                raise ValueError(f"Agent '{agent_id}' does not exist")

            refreshed = self._refresh_status(record)
            self._records[agent_id] = refreshed
            self._save_registry()

        if not refreshed.container_id:
            return refreshed, ""

        try:
            container = self._docker.containers.get(refreshed.container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return refreshed, logs.decode("utf-8", errors="replace")
        except NotFound:
            missing = ManagedAgentRecord(**{
                **asdict(refreshed),
                "container_id": None,
                "host_port": None,
                "status": "missing",
                "updated_at": self._now(),
            })
            with self._lock:
                self._records[agent_id] = missing
                self._save_registry()
            return missing, ""

    def _start_container(
        self,
        record: ManagedAgentRecord,
        *,
        extra_env: dict[str, str],
        command: list[str] | None,
    ) -> ManagedAgentRecord:
        inherited_env = {
            key: value
            for key in [
                "OPENROUTER_API_KEY",
                "OPENAI_API_KEY",
                "LANGFUSE_PUBLIC_KEY",
                "LANGFUSE_SECRET_KEY",
                "LANGFUSE_HOST",
                "LANGFUSE_BASE_URL",
                "BUDDY_ENV_IMAGE",
                "BUDDY_ENV_WARM_CONTAINERS",
            ]
            if (value := os.environ.get(key))
        }
        network_name = self._agent_network_name(record.agent_id)
        env_daemon_name = self._agent_env_daemon_name(record.agent_id)
        docker_host = f"tcp://{env_daemon_name}:2375"
        env = {
            "BUDDY_AGENT_CONFIG": record.config_mount_path,
            "DOCKER_HOST": docker_host,
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
        self._prune_stale_env_daemon_containers(record.agent_id)
        self._ensure_agent_network(record.agent_id)
        self._ensure_env_daemon_container(record.agent_id, network_name)

        port_key = f"{record.container_port}/tcp"
        container_name = self._agent_container_name(record.agent_id)
        created_container = False
        try:
            container = self._docker.containers.get(container_name)
            container.reload()
            if not self._runtime_container_compatible(container, (docker_host,), network_name):
                container.remove(force=True)
                raise NotFound("incompatible runtime container")
            if container.status != "running":
                container.start()
        except NotFound:
            container = self._docker.containers.run(
                record.image,
                detach=True,
                name=container_name,
                command=command,
                environment=env,
                network=network_name,
                ports={port_key: ("127.0.0.1", 0)},
                extra_hosts={"host.docker.internal": "host-gateway"},
                volumes={record.config_path: {"bind": record.config_mount_path, "mode": "ro"}},
                labels={
                    "buddy.managed_agent": "true",
                    "buddy.agent_id": record.agent_id,
                    "buddy.config_path": record.config_path,
                    "buddy.config_mount_path": record.config_mount_path,
                    "buddy.container_port": str(record.container_port),
                },
            )
            created_container = True

        container.reload()
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        bindings = ports.get(port_key)
        if not bindings:
            if created_container:
                container.remove(force=True)
            raise RuntimeError(f"Container for '{record.agent_id}' did not expose port {record.container_port}")
        host_port = int(bindings[0]["HostPort"])

        try:
            self._wait_for_a2a_ready(record.agent_id, host_port)
        except Exception as error:
            if created_container:
                container.remove(force=True)
            raise RuntimeError(f"Managed agent '{record.agent_id}' failed to become ready: {error}") from error

        return ManagedAgentRecord(**{
            **asdict(record),
            "container_id": container.id,
            "host_port": host_port,
            "status": container.status,
            "last_error": None,
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
                "last_error": None,
                "updated_at": self._now(),
            })

        status = container.status
        if status != "running":
            return ManagedAgentRecord(**{
                **asdict(record),
                "status": status,
                "last_error": None,
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
            "last_error": None,
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

    def reconcile_from_docker(self) -> list[ManagedAgentRecord]:
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
                    if not isinstance(config_path, str) or not isinstance(config_mount_path, str):
                        continue
                    try:
                        container_port = int(container_port_raw) if isinstance(container_port_raw, str) else 10001
                    except ValueError:
                        container_port = 10001
                    now = self._now()
                    image_obj = container.image
                    tags = image_obj.tags if image_obj is not None else []
                    existing = ManagedAgentRecord(
                        agent_id=agent_id,
                        image=tags[0] if tags else "unknown",
                        config_path=config_path,
                        config_mount_path=config_mount_path,
                        container_port=container_port,
                        container_id=container.id,
                        host_port=None,
                        status=container.status,
                        last_error=None,
                        created_at=now,
                        updated_at=now,
                    )

                refreshed = self._refresh_status(existing)
                if refreshed.container_id is None:
                    refreshed = ManagedAgentRecord(**{
                        **asdict(refreshed),
                        "container_id": container.id,
                        "status": container.status,
                        "updated_at": self._now(),
                    })
                    refreshed = self._refresh_status(refreshed)

                self._records[agent_id] = refreshed

            self._save_registry()
            return sorted(self._records.values(), key=lambda item: item.agent_id)

    def _validate_config(self, agent_id: str, config_yaml: str) -> None:
        try:
            config = parse_runtime_agent_config_yaml(config_yaml)
        except (TypeError, ValueError) as error:
            raise ValueError(str(error)) from error
        if config.agent.id != agent_id:
            raise ValueError(f"Config agent.id ('{config.agent.id}') must match managed agent id ('{agent_id}')")

    def _wait_for_a2a_ready(self, agent_id: str, host_port: int) -> None:
        base_url = f"http://127.0.0.1:{host_port}"
        delay = 0.2
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                agents_response = requests.get(f"{base_url}/agents", timeout=2)
                if agents_response.ok:
                    payload = agents_response.json()
                    if isinstance(payload, dict) and isinstance(payload.get("agents"), list):
                        return
            except requests.RequestException:
                pass
            sleep(delay)
            delay = min(delay * 2, 2.0)
        raise RuntimeError(f"Managed agent '{agent_id}' failed readiness check at {base_url}/agents")

    def _save_registry(self) -> None:
        payload = {agent_id: asdict(record) for agent_id, record in self._records.items()}
        self._registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _agent_container_name(self, agent_id: str) -> str:
        return f"buddy-agent-{self._slug(agent_id)}"

    def _agent_env_daemon_name(self, agent_id: str) -> str:
        return f"buddy-agent-env-{self._slug(agent_id)}"

    def _agent_network_name(self, agent_id: str) -> str:
        return f"buddy-agent-net-{self._slug(agent_id)}"

    def _ensure_agent_network(self, agent_id: str) -> None:
        network_name = self._agent_network_name(agent_id)
        try:
            self._docker.networks.get(network_name)
        except NotFound:
            self._docker.networks.create(
                network_name,
                driver="bridge",
                labels={
                    "buddy.managed_agent_network": "true",
                    "buddy.agent_id": agent_id,
                },
            )

    def _ensure_env_daemon_container(self, agent_id: str, network_name: str) -> None:
        daemon_name = self._agent_env_daemon_name(agent_id)
        daemon_image = os.environ.get("BUDDY_ENV_DAEMON_IMAGE", "docker:27-dind")

        try:
            env_daemon = self._docker.containers.get(daemon_name)
            env_daemon.reload()
            networks = env_daemon.attrs.get("NetworkSettings", {}).get("Networks", {})
            if network_name not in networks:
                network = self._docker.networks.get(network_name)
                network.connect(env_daemon)
            if env_daemon.status != "running":
                env_daemon.start()
            return
        except NotFound:
            pass

        self._docker.containers.run(
            daemon_image,
            detach=True,
            name=daemon_name,
            command=["dockerd", "--host=tcp://0.0.0.0:2375"],
            environment={"DOCKER_TLS_CERTDIR": ""},
            privileged=True,
            network=network_name,
            labels={
                "buddy.managed_agent_env_daemon": "true",
                "buddy.agent_id": agent_id,
            },
        )

    @staticmethod
    def _runtime_container_compatible(
        container,
        expected_docker_hosts: tuple[str, ...],
        network_name: str,
    ) -> bool:
        container_env = container.attrs.get("Config", {}).get("Env", [])
        if not isinstance(container_env, list):
            return False

        if expected_docker_hosts:
            expected_entries = {f"DOCKER_HOST={value}" for value in expected_docker_hosts}
            if not any(entry in container_env for entry in expected_entries):
                return False

        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        if network_name not in networks:
            return False

        return True

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

    def _prune_stale_env_daemon_containers(self, agent_id: str) -> None:
        canonical_name = self._agent_env_daemon_name(agent_id)
        daemon_containers = self._docker.containers.list(
            all=True,
            filters={"label": ["buddy.managed_agent_env_daemon=true", f"buddy.agent_id={agent_id}"]},
        )
        for container in daemon_containers:
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
        return datetime.now(tz=UTC).isoformat()
