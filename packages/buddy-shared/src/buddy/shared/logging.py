import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

_LOGGER_NAME = "buddy"
_HANDLER_MARKER = "_buddy_structured_handler"
_service_name = _LOGGER_NAME
_request_id_var: ContextVar[str | None] = ContextVar("buddy_request_id", default=None)


def configure_logging(service_name: str, level: str | int | None = None) -> logging.Logger:
    global _service_name
    _service_name = service_name

    logger = logging.getLogger(_LOGGER_NAME)
    resolved_level = _resolve_level(level or os.environ.get("BUDDY_LOG_LEVEL", "INFO"))
    logger.setLevel(resolved_level)
    logger.propagate = False

    handler = next((item for item in logger.handlers if getattr(item, _HANDLER_MARKER, False)), None)
    if handler is None:
        handler = logging.StreamHandler()
        setattr(handler, _HANDLER_MARKER, True)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    handler.setLevel(resolved_level)
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


@contextmanager
def request_logging_context(request_id: str | None) -> Iterator[None]:
    token: Token[str | None] = _request_id_var.set(request_id)
    try:
        yield
    finally:
        _request_id_var.reset(token)


def emit_event(
    logger: logging.Logger,
    event: str,
    *,
    level: str | int = logging.INFO,
    **fields: Any,
) -> None:
    payload = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "service": _service_name,
        "event": event,
        "service_version": os.environ.get("BUDDY_SERVICE_VERSION"),
        "commit_hash": os.environ.get("BUDDY_COMMIT_HASH"),
        "environment": os.environ.get("BUDDY_ENVIRONMENT"),
        "region": os.environ.get("BUDDY_REGION"),
        "instance_id": os.environ.get("BUDDY_INSTANCE_ID"),
    }

    request_id = _request_id_var.get()
    if request_id and "request_id" not in fields:
        payload["request_id"] = request_id

    for key, value in fields.items():
        if value is not None:
            payload[key] = value

    logger.log(_resolve_level(level), json.dumps(payload, default=_json_default, sort_keys=True))


def _resolve_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    resolved = logging.getLevelName(level.upper())
    if isinstance(resolved, int):
        return resolved
    return logging.INFO


def _json_default(value: object) -> object:
    if isinstance(value, set):
        return sorted(value)
    return str(value)
