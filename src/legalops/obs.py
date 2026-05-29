"""Structured JSON logging helper for LegalOps BR.

Provides JSON-formatted logger with LGPD-aware PII filtering.

Env vars:
    LEGALOPS_LOG_LEVEL: log level (default INFO)
    LEGALOPS_LOG_JSON: "1" to enable JSON format, otherwise plain text

Uso:
    >>> from legalops.obs import get_logger
    >>> log = get_logger("legalops.pipeline")
    >>> log.info("processed", extra={"n": 5})
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
from datetime import UTC, datetime
from typing import Any

# LGPD: subset duplicado de pii_redactor.PATTERNS — strip PII de mensagens/extras de log.
_LGPD_FILTERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),  # CNPJ
    re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),  # CPF
    re.compile(r"\bOAB[/-]?[A-Z]{2}\s?\d{1,6}\b"),  # OAB
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),  # EMAIL
    re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    ),  # PIX_UUID
)

_REDACT_TOKEN = "***REDACTED***"  # noqa: S105 - LGPD redaction marker, not a credential

_CONFIGURED = False
_LOCK = threading.Lock()

_RESERVED_LOGRECORD_KEYS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }
)


def _scrub(value: Any) -> Any:
    """Strip PII matches from any str inside value (recursive over dict/list)."""
    if isinstance(value, str):
        out = value
        for pat in _LGPD_FILTERS:
            out = pat.sub(_REDACT_TOKEN, out)
        return out
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        scrubbed = [_scrub(v) for v in value]
        return type(value)(scrubbed) if isinstance(value, tuple) else scrubbed
    return value


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter with LGPD-aware PII stripping."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=UTC).isoformat()
        msg = _scrub(record.getMessage())

        extra: dict[str, Any] = {}
        for key, val in record.__dict__.items():
            if key in _RESERVED_LOGRECORD_KEYS or key.startswith("_"):
                continue
            extra[key] = _scrub(val)

        payload: dict[str, Any] = {
            "ts": ts,
            "level": record.levelname,
            "logger": record.name,
            "msg": msg,
            "extra": extra,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class _PlainScrubFormatter(logging.Formatter):
    """Plain text fallback que ainda scrub-a PII."""

    def format(self, record: logging.LogRecord) -> str:
        record.msg = _scrub(record.getMessage())
        record.args = ()
        return super().format(record)


def _build_handler() -> logging.Handler:
    use_json = os.environ.get("LEGALOPS_LOG_JSON", "0") == "1"
    handler = logging.StreamHandler(stream=sys.stderr)
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            _PlainScrubFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s — %(message)s",
            )
        )
    return handler


def _configure_once() -> None:
    global _CONFIGURED
    with _LOCK:
        if _CONFIGURED:
            return
        level_name = os.environ.get("LEGALOPS_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
        root = logging.getLogger("legalops")
        # Remove handlers anteriores (re-config defensiva em testes)
        for h in list(root.handlers):
            root.removeHandler(h)
        root.addHandler(_build_handler())
        root.setLevel(level)
        root.propagate = False
        _CONFIGURED = True


def reset_for_tests() -> None:
    """Forca reconfigure no proximo get_logger. Apenas testes."""
    global _CONFIGURED
    with _LOCK:
        _CONFIGURED = False
        root = logging.getLogger("legalops")
        for h in list(root.handlers):
            root.removeHandler(h)


def get_logger(name: str) -> logging.Logger:
    """Return configured stdlib logger. Idempotent."""
    _configure_once()
    if name == "legalops" or name.startswith("legalops."):
        return logging.getLogger(name)
    return logging.getLogger(f"legalops.{name}")
