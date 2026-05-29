"""Tests for legalops.obs — structured JSON logging + LGPD filter."""

from __future__ import annotations

import io
import json
import logging
import os
from typing import Any

import pytest

from legalops import obs


@pytest.fixture(autouse=True)
def _reset_obs() -> Any:
    obs.reset_for_tests()
    yield
    obs.reset_for_tests()


def _capture(
    monkeypatch: pytest.MonkeyPatch, name: str = "test"
) -> tuple[logging.Logger, io.StringIO]:
    monkeypatch.setenv("LEGALOPS_LOG_JSON", "1")
    monkeypatch.setenv("LEGALOPS_LOG_LEVEL", "DEBUG")
    log = obs.get_logger(name)
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(obs.JsonFormatter())
    log.addHandler(handler)
    return log, buf


def test_json_formatter_basic_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    log, buf = _capture(monkeypatch, "fmt_basic")

    # Act
    log.info("hello", extra={"n": 5})

    # Assert
    line = buf.getvalue().strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["msg"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["logger"].endswith("fmt_basic")
    assert "ts" in payload and "T" in payload["ts"]
    assert payload["extra"]["n"] == 5


def test_get_logger_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("LEGALOPS_LOG_JSON", "1")

    # Act
    a = obs.get_logger("idem")
    b = obs.get_logger("idem")
    root = logging.getLogger("legalops")
    n_handlers = len(root.handlers)
    obs.get_logger("idem2")
    n_after = len(root.handlers)

    # Assert
    assert a is b
    assert n_handlers == n_after  # configure_once nao adiciona handlers extras


def test_lgpd_filter_strips_cpf(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    log, buf = _capture(monkeypatch, "lgpd_cpf")

    # Act
    log.info("CPF 123.456.789-09 detectado", extra={"raw": "também 987.654.321-00"})

    # Assert
    out = buf.getvalue()
    assert "123.456.789-09" not in out
    assert "987.654.321-00" not in out
    assert "REDACTED" in out


def test_lgpd_filter_strips_email(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    log, buf = _capture(monkeypatch, "lgpd_email")

    # Act
    log.warning("contato user@example.com agora")

    # Assert
    out = buf.getvalue()
    assert "user@example.com" not in out
    assert "REDACTED" in out


def test_lgpd_filter_strips_cnpj_and_oab(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    log, buf = _capture(monkeypatch, "lgpd_cnpj")

    # Act
    log.info("CNPJ 12.345.678/0001-90 advogado OAB/PR 12345")

    # Assert
    out = buf.getvalue()
    assert "12.345.678/0001-90" not in out
    assert "OAB/PR 12345" not in out


def test_env_log_level_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("LEGALOPS_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("LEGALOPS_LOG_JSON", "1")

    # Act
    log = obs.get_logger("level_test")
    root = logging.getLogger("legalops")

    # Assert
    assert root.level == logging.WARNING
    assert log.isEnabledFor(logging.WARNING)
    assert not log.isEnabledFor(logging.DEBUG)


def test_plain_text_mode_default(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("LEGALOPS_LOG_JSON", raising=False)

    # Act
    obs.get_logger("plain")
    root = logging.getLogger("legalops")
    fmt = root.handlers[0].formatter

    # Assert
    assert not isinstance(fmt, obs.JsonFormatter)


def test_scrub_handles_nested_dict() -> None:
    # Arrange
    data = {"user": {"cpf": "123.456.789-09", "name": "alice"}}

    # Act
    out = obs._scrub(data)

    # Assert
    assert isinstance(out, dict)
    assert out["user"]["cpf"] != "123.456.789-09"
    assert out["user"]["name"] == "alice"


def test_env_var_unset_defaults_info(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("LEGALOPS_LOG_LEVEL", raising=False)
    monkeypatch.delenv("LEGALOPS_LOG_JSON", raising=False)

    # Act
    obs.get_logger("default_lvl")
    root = logging.getLogger("legalops")

    # Assert
    assert root.level == logging.INFO
    assert os.environ.get("LEGALOPS_LOG_LEVEL") is None
