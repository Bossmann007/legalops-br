"""Tests pra helpers internos do CLI + comandos pouco exercitados.

Foca cobrir caminhos que tests/test_cli.py via main() nao toca:
- `_make_redactor` (faltando salt)
- `cmd_audit_verify` (chain valida + invalida)
- `cmd_health` (text/json/metrics, com e sem audit-db)
- `cmd_metrics` (rendering Prometheus)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pytest

from legalops.cli import (
    _make_redactor,
    _run_health_checks,
    cmd_audit_verify,
    cmd_health,
    cmd_metrics,
    main,
)
from legalops.oab_sigilo import AuditLog
from legalops.pii_redactor import SALT_ENV_VAR


class TestMakeRedactor:
    def test_missing_salt_exits_2(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(SALT_ENV_VAR, raising=False)
        with pytest.raises(SystemExit) as exc:
            _make_redactor()
        assert exc.value.code == 2

    def test_with_salt_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SALT_ENV_VAR, "ci-synthetic-salt-32-bytes-fixture")
        r = _make_redactor()
        assert r is not None


class TestCmdAuditVerify:
    def test_valid_chain_returns_0(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        db = tmp_path / "audit.db"
        log = AuditLog(db)
        log.append("agent:test", "redact", "res:1", {"k": "v"})
        log.append("agent:test", "redact", "res:2", {"k": "v2"})

        ns = argparse.Namespace(db=str(db))
        rc = cmd_audit_verify(ns)
        out = json.loads(capsys.readouterr().out)

        assert rc == 0
        assert out["valid"] is True
        assert out["entries"] == 2

    def test_tampered_chain_returns_1(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        db = tmp_path / "audit.db"
        log = AuditLog(db)
        log.append("agent:test", "redact", "res:1", {"k": "v"})
        log.append("agent:test", "redact", "res:2", {"k": "v2"})
        with sqlite3.connect(db) as conn:
            conn.execute(
                "UPDATE audit_log SET metadata = ? WHERE seq = ?",
                ('{"k":"tampered"}', 1),
            )
            conn.commit()

        ns = argparse.Namespace(db=str(db))
        rc = cmd_audit_verify(ns)
        out = json.loads(capsys.readouterr().out)

        assert rc == 1
        assert out["valid"] is False


class TestCmdHealth:
    def test_healthy_text_format(self, capsys: pytest.CaptureFixture) -> None:
        ns = argparse.Namespace(audit_db=None, format="text", metrics=False)
        rc = cmd_health(ns)
        captured = capsys.readouterr().out
        assert rc == 0
        assert "status: healthy" in captured
        assert "pii_redactor" in captured

    def test_healthy_json_format(self, capsys: pytest.CaptureFixture) -> None:
        ns = argparse.Namespace(audit_db=None, format="json", metrics=False)
        rc = cmd_health(ns)
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert out["status"] == "healthy"
        names = [c["name"] for c in out["checks"]]
        assert "pii_redactor" in names
        assert "cpc_prazos" in names
        assert "tribunal_detector" in names

    def test_with_audit_db(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        db = tmp_path / "audit.db"
        AuditLog(db).append("agent:t", "redact", "res:1", {})
        ns = argparse.Namespace(audit_db=str(db), format="json", metrics=False)
        rc = cmd_health(ns)
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        names = [c["name"] for c in out["checks"]]
        assert "audit_chain" in names

    def test_with_metrics_render(self, capsys: pytest.CaptureFixture) -> None:
        ns = argparse.Namespace(audit_db=None, format="text", metrics=True)
        rc = cmd_health(ns)
        captured = capsys.readouterr().out
        assert rc == 0
        assert "--- metrics ---" in captured
        assert "legalops_healthcheck_total" in captured


class TestRunHealthChecks:
    def test_returns_checks_and_registry(self) -> None:
        checks, registry = _run_health_checks(None)
        assert len(checks) >= 3
        assert all("name" in c and "ok" in c and "ms" in c for c in checks)
        # registry exposes Prometheus output
        text = registry.render()
        assert "legalops_healthcheck_total" in text


class TestCmdMetrics:
    def test_renders_prometheus_exposition(self, capsys: pytest.CaptureFixture) -> None:
        ns = argparse.Namespace()
        rc = cmd_metrics(ns)
        out = capsys.readouterr().out
        assert rc == 0
        assert "legalops_pipeline_runs_total" in out
        assert "legalops_intimacoes_processed_total" in out


class TestCmdHealthEntryPoint:
    """Exercita health pelo entry-point main() pra cobrir argparse wiring."""

    def test_main_health_json(self, capsys: pytest.CaptureFixture) -> None:
        rc = main(["health", "--format", "json"])
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert "status" in out
