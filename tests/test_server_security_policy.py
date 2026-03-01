import pytest

from buddy.a2a.server import _enforce_internal_token_policy


def test_token_policy_allows_local_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BUDDY_ENV", raising=False)
    monkeypatch.delenv("BUDDY_ALLOW_INSECURE_INTERNAL_RUNTIME", raising=False)
    _enforce_internal_token_policy("http://localhost:10001", token=None)


def test_token_policy_rejects_non_local_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BUDDY_ENV", raising=False)
    monkeypatch.delenv("BUDDY_ALLOW_INSECURE_INTERNAL_RUNTIME", raising=False)
    with pytest.raises(RuntimeError):
        _enforce_internal_token_policy("https://buddy.example.com", token=None)


def test_token_policy_allows_non_local_with_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BUDDY_ENV", raising=False)
    monkeypatch.delenv("BUDDY_ALLOW_INSECURE_INTERNAL_RUNTIME", raising=False)
    _enforce_internal_token_policy("https://buddy.example.com", token="secret")
