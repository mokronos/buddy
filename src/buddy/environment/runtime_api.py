import requests

from buddy.environment.runtime import ExecResult


class RuntimeAPIEnvironmentManager:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def acquire(self, owner_id: str) -> dict[str, str]:
        payload = self._post("/internal/runtime/acquire", {"owner_id": owner_id})
        container_id = payload.get("containerId")
        if not isinstance(container_id, str):
            raise TypeError("Invalid acquire response from runtime API")
        return {
            "owner_id": owner_id,
            "container_id": container_id,
        }

    def release(self, owner_id: str, reusable: bool = True) -> None:
        self._post(
            "/internal/runtime/release",
            {
                "owner_id": owner_id,
                "reusable": reusable,
            },
        )

    def exec(self, owner_id: str, command: str, timeout_s: int = 30) -> ExecResult:
        payload = self._post(
            "/internal/runtime/exec",
            {
                "owner_id": owner_id,
                "command": command,
                "timeout_s": timeout_s,
            },
        )

        exit_code = payload.get("exitCode")
        stdout = payload.get("stdout")
        stderr = payload.get("stderr")
        if not isinstance(exit_code, int) or not isinstance(stdout, str) or not isinstance(stderr, str):
            raise TypeError("Invalid exec response from runtime API")

        return ExecResult(exit_code=exit_code, stdout=stdout, stderr=stderr)

    def read_file(self, owner_id: str, path: str) -> str:
        payload = self._post(
            "/internal/runtime/read-file",
            {
                "owner_id": owner_id,
                "path": path,
            },
        )
        content = payload.get("content")
        if not isinstance(content, str):
            raise TypeError("Invalid read-file response from runtime API")
        return content

    def write_file(self, owner_id: str, path: str, content: str) -> None:
        self._post(
            "/internal/runtime/write-file",
            {
                "owner_id": owner_id,
                "path": path,
                "content": content,
            },
        )

    def patch_file(self, owner_id: str, path: str, old_text: str, new_text: str, count: int = 1) -> int:
        payload = self._post(
            "/internal/runtime/patch-file",
            {
                "owner_id": owner_id,
                "path": path,
                "old_text": old_text,
                "new_text": new_text,
                "count": count,
            },
        )
        replacements = payload.get("replacements")
        if not isinstance(replacements, int):
            raise TypeError("Invalid patch-file response from runtime API")
        return replacements

    def _post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        headers: dict[str, str] = {}
        if self.token:
            headers["x-buddy-internal-token"] = self.token

        response = requests.post(
            f"{self.base_url}{path}",
            json=payload,
            headers=headers,
            timeout=60,
        )

        if not response.ok:
            raise RuntimeError(f"Runtime API request failed ({response.status_code}): {response.text}")

        body = response.json()
        if not isinstance(body, dict):
            raise TypeError("Runtime API returned invalid JSON payload")
        return body
