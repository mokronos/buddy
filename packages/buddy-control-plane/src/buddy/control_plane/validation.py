import ipaddress
import re
from urllib.parse import urlparse

_AGENT_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def validate_agent_id(agent_id: str) -> str:
    normalized = agent_id.strip().lower()
    if not normalized:
        raise ValueError("Agent id is required")
    if not _AGENT_ID_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Invalid agent id. Use lowercase letters, numbers, and '-', start/end with alphanumeric, max length 63"
        )
    return normalized


def derive_agent_id_from_name(name: str) -> str:
    normalized_name = name.strip().lower()
    if not normalized_name:
        raise ValueError("Agent name is required")

    candidate = re.sub(r"[^a-z0-9]+", "-", normalized_name).strip("-")
    candidate = candidate[:63].strip("-")
    if not candidate:
        raise ValueError("Agent name must include at least one letter or number")
    return validate_agent_id(candidate)


def normalize_external_base_url(base_url: str, *, allow_private_hosts: bool = True) -> str:
    normalized = base_url.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("External URL must be a valid http(s) URL")
    if parsed.username or parsed.password:
        raise ValueError("External URL must not include user credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("External URL must not include query string or fragment")

    host = parsed.hostname
    if host is None:
        raise ValueError("External URL is missing hostname")

    if not allow_private_hosts:
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            ip = None
        if ip is not None and (ip.is_private or ip.is_loopback or ip.is_link_local):
            raise ValueError("External URL host must not be private/loopback in this environment")

    return normalized
