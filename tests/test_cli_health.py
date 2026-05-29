"""Tests for `legalops health` and `legalops metrics` CLI subcommands."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from legalops.cli import main


def _run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    return code, buf.getvalue()


def test_health_text_exits_zero() -> None:
    # Arrange / Act
    code, out = _run(["health"])

    # Assert
    assert code == 0
    assert "status: healthy" in out
    assert "pii_redactor" in out
    assert "cpc_prazos" in out
    assert "tribunal_detector" in out


def test_health_json_structure() -> None:
    # Arrange / Act
    code, out = _run(["health", "--format", "json"])

    # Assert
    assert code == 0
    payload = json.loads(out)
    assert payload["status"] == "healthy"
    names = {c["name"] for c in payload["checks"]}
    assert {"pii_redactor", "cpc_prazos", "tribunal_detector"} <= names
    for c in payload["checks"]:
        assert c["ok"] is True
        assert isinstance(c["ms"], (int, float))


def test_health_with_audit_db(tmp_path: Path) -> None:
    # Arrange — create real audit log so chain verifies
    from legalops.oab_sigilo import AuditLog

    db = tmp_path / "audit.db"
    log = AuditLog(db)
    log.append(action="test", resource="r1", actor="tester", metadata={})

    # Act
    code, out = _run(["health", "--format", "json", "--audit-db", str(db)])

    # Assert
    assert code == 0
    payload = json.loads(out)
    names = {c["name"] for c in payload["checks"]}
    assert "audit_chain" in names


def test_health_metrics_flag_renders_exposition() -> None:
    # Arrange / Act
    code, out = _run(["health", "--metrics"])

    # Assert
    assert code == 0
    assert "--- metrics ---" in out
    assert "legalops_healthcheck_total" in out
    assert "# TYPE legalops_healthcheck_total counter" in out


def test_metrics_subcommand_outputs_exposition() -> None:
    # Arrange / Act
    code, out = _run(["metrics"])

    # Assert
    assert code == 0
    assert "# TYPE legalops_pipeline_runs_total counter" in out
    assert "legalops_pipeline_runs_total" in out


@pytest.mark.parametrize("fmt", ["json", "text"])
def test_health_format_flag_accepts(fmt: str) -> None:
    # Arrange / Act
    code, _ = _run(["health", "--format", fmt])

    # Assert
    assert code == 0
