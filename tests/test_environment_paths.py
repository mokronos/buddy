import pytest

from buddy.environment.manager import EnvironmentManager


def _manager_for_path_tests() -> EnvironmentManager:
    manager = object.__new__(EnvironmentManager)
    manager.workspace_dir = "/workspace"
    return manager


def test_resolve_relative_path() -> None:
    manager = _manager_for_path_tests()
    assert manager._resolve_path("src/main.py") == "/workspace/src/main.py"


def test_resolve_rejects_path_traversal() -> None:
    manager = _manager_for_path_tests()
    with pytest.raises(ValueError):
        manager._resolve_path("../etc/passwd")


def test_resolve_rejects_absolute_outside_workspace() -> None:
    manager = _manager_for_path_tests()
    with pytest.raises(ValueError):
        manager._resolve_path("/etc/passwd")
