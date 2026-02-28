from dataclasses import dataclass
from typing import Protocol


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str


class EnvironmentRuntime(Protocol):
    def acquire(self, owner_id: str) -> object: ...

    def release(self, owner_id: str, reusable: bool = True) -> None: ...

    def exec(self, owner_id: str, command: str, timeout_s: int = 30) -> ExecResult: ...

    def read_file(self, owner_id: str, path: str) -> str: ...

    def write_file(self, owner_id: str, path: str, content: str) -> None: ...

    def patch_file(self, owner_id: str, path: str, old_text: str, new_text: str, count: int = 1) -> int: ...
