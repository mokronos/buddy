import io
import posixpath
import shlex
import tarfile
from collections import deque
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

import docker
from docker.errors import ImageNotFound, NotFound
from docker.models.containers import Container

from buddy.environment.runtime import ExecResult


@dataclass
class EnvironmentLease:
    owner_id: str
    container_id: str


class EnvironmentManager:
    def __init__(
        self,
        image_ref: str,
        warm_containers: int = 1,
        workspace_dir: str = "/workspace",
        name_prefix: str = "buddy-environment",
    ) -> None:
        self.image_ref = image_ref
        self.warm_containers = max(0, warm_containers)
        self.workspace_dir = workspace_dir.rstrip("/") or "/workspace"
        self.name_prefix = name_prefix
        self.keepalive_command = ["sh", "-lc", "while true; do sleep 3600; done"]

        self._docker = docker.from_env()
        self._lock = Lock()
        self._leases: dict[str, str] = {}
        self._idle: deque[str] = deque()
        self._owner_indices: dict[str, int] = {}

    def start(self) -> None:
        self._ensure_image_exists()
        with self._lock:
            missing = max(0, self.warm_containers - len(self._idle))
            for _ in range(missing):
                container = self._create_container()
                self._idle.append(self._container_id(container))

    def stop(self) -> None:
        with self._lock:
            container_ids = set(self._idle)
            container_ids.update(self._leases.values())
            self._idle.clear()
            self._leases.clear()

        for container_id in container_ids:
            try:
                container = self._docker.containers.get(container_id)
                container.remove(force=True)
            except NotFound:
                continue

    def acquire(self, owner_id: str) -> EnvironmentLease:
        with self._lock:
            leased_container_id = self._leases.get(owner_id)
            if leased_container_id:
                container = self._ensure_running(leased_container_id)
                container_id = self._container_id(container)
                self._leases[owner_id] = container_id
                return EnvironmentLease(owner_id=owner_id, container_id=container_id)

            container = self._acquire_idle_container()
            self._rename_container_for_owner(container, owner_id)
            container_id = self._container_id(container)
            self._leases[owner_id] = container_id
            return EnvironmentLease(owner_id=owner_id, container_id=container_id)

    def release(self, owner_id: str, reusable: bool = True) -> None:
        with self._lock:
            container_id = self._leases.pop(owner_id, None)
            if container_id is None:
                return

            if reusable:
                container = self._ensure_running(container_id)
                self._idle.append(self._container_id(container))
                return

        try:
            container = self._docker.containers.get(container_id)
            container.remove(force=True)
        except NotFound:
            return

    def exec(self, owner_id: str, command: str, timeout_s: int = 30) -> ExecResult:
        lease = self.acquire(owner_id)
        container = self._docker.containers.get(lease.container_id)
        result = container.exec_run(
            ["sh", "-lc", command],
            demux=True,
            workdir=self.workspace_dir,
            stdout=True,
            stderr=True,
        )
        stdout_bytes, stderr_bytes = result.output if result.output else (b"", b"")
        stdout = (stdout_bytes or b"").decode("utf-8", errors="replace")
        stderr = (stderr_bytes or b"").decode("utf-8", errors="replace")
        return ExecResult(exit_code=result.exit_code, stdout=stdout, stderr=stderr)

    def read_file(self, owner_id: str, path: str) -> str:
        lease = self.acquire(owner_id)
        container = self._docker.containers.get(lease.container_id)
        absolute_path = self._resolve_path(path)
        stream, _ = container.get_archive(absolute_path)
        archive_bytes = b"".join(stream)

        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
            members = archive.getmembers()
            if not members:
                raise FileNotFoundError(f"No archive content found at {absolute_path}")
            member = members[0]
            file_obj = archive.extractfile(member)
            if file_obj is None:
                raise IsADirectoryError(f"Path is not a file: {absolute_path}")
            return file_obj.read().decode("utf-8", errors="replace")

    def write_file(self, owner_id: str, path: str, content: str) -> None:
        lease = self.acquire(owner_id)
        container = self._docker.containers.get(lease.container_id)
        absolute_path = self._resolve_path(path)
        parent_dir = posixpath.dirname(absolute_path)
        file_name = posixpath.basename(absolute_path)

        mkdir_command = f"mkdir -p {shlex.quote(parent_dir)}"
        mkdir_result = container.exec_run(["sh", "-lc", mkdir_command])
        if mkdir_result.exit_code != 0:
            output = (mkdir_result.output or b"").decode("utf-8", errors="replace")
            raise RuntimeError(f"Failed to create parent directory for {absolute_path}: {output}")

        tar_buffer = io.BytesIO()
        payload = content.encode("utf-8")
        with tarfile.open(fileobj=tar_buffer, mode="w") as archive:
            info = tarfile.TarInfo(name=file_name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

        tar_buffer.seek(0)
        container.put_archive(parent_dir, tar_buffer.getvalue())

    def patch_file(self, owner_id: str, path: str, old_text: str, new_text: str, count: int = 1) -> int:
        if count <= 0:
            raise ValueError("count must be greater than 0")

        current_content = self.read_file(owner_id, path)
        replacements = current_content.count(old_text)
        if replacements == 0:
            raise ValueError(f"Could not find requested text to patch in {path}")

        applied = min(replacements, count)
        updated_content = current_content.replace(old_text, new_text, count)
        self.write_file(owner_id, path, updated_content)
        return applied

    def _acquire_idle_container(self) -> Container:
        while self._idle:
            container_id = self._idle.popleft()
            try:
                return self._ensure_running(container_id)
            except NotFound:
                continue
        return self._create_container()

    def _ensure_image_exists(self) -> None:
        try:
            self._docker.images.get(self.image_ref)
        except ImageNotFound as error:
            raise RuntimeError(
                f"Docker image '{self.image_ref}' is not built. Build it before starting Buddy."
            ) from error

    def _create_container(self) -> Container:
        return self._docker.containers.run(
            self.image_ref,
            detach=True,
            name=f"{self.name_prefix}-{uuid4().hex[:8]}",
            command=self.keepalive_command,
            labels={
                "buddy.environment": "true",
                "buddy.profile": "environment",
            },
        )

    def _ensure_running(self, container_id: str) -> Container:
        container = self._docker.containers.get(container_id)
        container.reload()
        if container.status != "running":
            current_cmd = container.attrs.get("Config", {}).get("Cmd") or []
            if current_cmd != self.keepalive_command:
                container.remove(force=True)
                return self._create_container()
            container.start()
            container.reload()
        if container.status != "running":
            container.remove(force=True)
            return self._create_container()
        return container

    def _resolve_path(self, path: str) -> str:
        cleaned = path.strip()
        if not cleaned:
            raise ValueError("path cannot be empty")

        normalized = posixpath.normpath(cleaned)
        if normalized == ".":
            return self.workspace_dir

        if normalized.startswith("/"):
            if normalized == self.workspace_dir or normalized.startswith(f"{self.workspace_dir}/"):
                return normalized
            raise ValueError("absolute paths must stay inside /workspace")

        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("path traversal is not allowed")

        return posixpath.normpath(f"{self.workspace_dir}/{normalized}")

    def _rename_container_for_owner(self, container: Container, owner_id: str) -> None:
        owner_name = owner_id.split(":", 1)[0]
        safe_owner = self._slug(owner_name)
        next_index = self._owner_indices.get(safe_owner, 0) + 1

        while True:
            candidate = f"buddy-env-{safe_owner}-{next_index}"
            try:
                self._docker.containers.get(candidate)
                next_index += 1
                continue
            except NotFound:
                pass

            container.rename(candidate)
            self._owner_indices[safe_owner] = next_index
            return

    @staticmethod
    def _container_id(container: Container) -> str:
        container_id = container.id
        if container_id is None:
            raise RuntimeError("Container id is missing")
        return container_id

    @staticmethod
    def _slug(value: str) -> str:
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
        return slug or "agent"
