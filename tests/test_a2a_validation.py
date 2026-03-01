import pytest

from buddy.a2a.validation import normalize_external_base_url, validate_agent_id


def test_validate_agent_id_accepts_slug() -> None:
    assert validate_agent_id("demo-agent") == "demo-agent"


def test_validate_agent_id_normalizes_case() -> None:
    assert validate_agent_id("Demo-Agent") == "demo-agent"


def test_validate_agent_id_rejects_invalid_chars() -> None:
    with pytest.raises(ValueError):
        validate_agent_id("demo_agent")


def test_external_url_rejects_query_and_fragment() -> None:
    with pytest.raises(ValueError):
        normalize_external_base_url("https://example.com/path?x=1")


def test_external_url_rejects_private_ip_when_disabled() -> None:
    with pytest.raises(ValueError):
        normalize_external_base_url("http://127.0.0.1:10001", allow_private_hosts=False)
