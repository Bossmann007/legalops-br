"""Tests pra helpers internos do CLI + comandos pouco exercitados.

Foca cobrir caminhos que tests/test_cli.py via main() nao toca:
- `_parse_channels_arg` / `_parse_hhmm_arg`
- `_build_multiplex_from_args` (erros e wiring de cada canal)
- `_make_redactor` (faltando salt)
- `cmd_audit_verify` (chain valida + invalida)
- `cmd_health` (text/json/metrics, com e sem audit-db)
- `cmd_metrics` (rendering Prometheus)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import time
from pathlib import Path
from typing import Any

import pytest

from legalops.cli import (
    _build_multiplex_from_args,
    _make_redactor,
    _parse_channels_arg,
    _parse_hhmm_arg,
    _run_health_checks,
    cmd_audit_verify,
    cmd_health,
    cmd_metrics,
    main,
)
from legalops.config import LegalOpsConfig
from legalops.oab_sigilo import AuditLog
from legalops.pii_redactor import SALT_ENV_VAR


class TestParseChannelsArg:
    def test_empty_returns_empty(self) -> None:
        assert _parse_channels_arg(None) == []
        assert _parse_channels_arg("") == []

    def test_single_channel(self) -> None:
        assert _parse_channels_arg("whatsapp") == ["whatsapp"]

    def test_multiple_normalized(self) -> None:
        assert _parse_channels_arg("WhatsApp, EMAIL ,slack") == [
            "whatsapp",
            "email",
            "slack",
        ]

    def test_blank_parts_skipped(self) -> None:
        assert _parse_channels_arg(",whatsapp,, ,email,") == ["whatsapp", "email"]

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="canal invalido"):
            _parse_channels_arg("whatsapp,carrier-pigeon")


class TestParseHhmmArg:
    def test_none(self) -> None:
        assert _parse_hhmm_arg(None) is None
        assert _parse_hhmm_arg("") is None

    def test_valid(self) -> None:
        assert _parse_hhmm_arg("22:00") == time(22, 0)
        assert _parse_hhmm_arg("06:30") == time(6, 30)

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match="HH:MM"):
            _parse_hhmm_arg("abc")

    def test_invalid_hour_raises(self) -> None:
        with pytest.raises(ValueError, match="HH:MM"):
            _parse_hhmm_arg("25:00")


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


class TestBuildMultiplexFromArgs:
    def _ns(self, **kw: Any) -> argparse.Namespace:
        defaults: dict[str, Any] = {
            "quiet_start": None,
            "quiet_end": None,
            "min_prazo_days": None,
            "chat_id": None,
            "bridge_url": None,
            "timeout": None,
        }
        defaults.update(kw)
        return argparse.Namespace(**defaults)

    def test_whatsapp_missing_chat_id_raises(self) -> None:
        cfg = LegalOpsConfig()
        with pytest.raises(ValueError, match="chat_id"):
            _build_multiplex_from_args(self._ns(), cfg, ["whatsapp"])

    def test_email_missing_smtp_raises(self) -> None:
        cfg = LegalOpsConfig()
        with pytest.raises(ValueError, match="smtp_host|from_addr|to_addr"):
            _build_multiplex_from_args(self._ns(), cfg, ["email"])

    def test_slack_missing_webhook_raises(self) -> None:
        cfg = LegalOpsConfig()
        with pytest.raises(ValueError, match="webhook_url"):
            _build_multiplex_from_args(self._ns(), cfg, ["slack"])

    def test_whatsapp_wired_when_chat_id_present(self) -> None:
        ns = self._ns(chat_id="5541999999999@s.whatsapp.net")
        cfg = LegalOpsConfig()
        mux = _build_multiplex_from_args(ns, cfg, ["whatsapp"])
        # Trava o canal certo: regressao conectando "email" pra "whatsapp" passaria sem isto.
        assert mux.channels == ["whatsapp"]

    def test_email_wired_when_cfg_complete(self) -> None:
        cfg = LegalOpsConfig(
            email_smtp_host="smtp.test.local",
            email_from_addr="bot@test.local",
            email_to_addr="user@test.local",
        )
        mux = _build_multiplex_from_args(self._ns(), cfg, ["email"])
        assert mux.channels == ["email"]

    def test_slack_wired_when_webhook_present(self) -> None:
        cfg = LegalOpsConfig(slack_webhook_url="https://hooks.slack.test/abc")
        mux = _build_multiplex_from_args(self._ns(), cfg, ["slack"])
        assert mux.channels == ["slack"]

    def test_multi_channel_wired_in_order(self) -> None:
        ns = self._ns(chat_id="5541999999999@s.whatsapp.net")
        cfg = LegalOpsConfig(
            email_smtp_host="smtp.test.local",
            email_from_addr="bot@test.local",
            email_to_addr="user@test.local",
            slack_webhook_url="https://hooks.slack.test/abc",
        )
        mux = _build_multiplex_from_args(ns, cfg, ["whatsapp", "email", "slack"])
        assert mux.channels == ["whatsapp", "email", "slack"]

    def test_quiet_hours_from_args_take_precedence(self) -> None:
        ns = self._ns(
            chat_id="x@s.whatsapp.net",
            quiet_start="23:00",
            quiet_end="07:00",
            min_prazo_days=5,
        )
        cfg = LegalOpsConfig()
        mux = _build_multiplex_from_args(ns, cfg, ["whatsapp"])
        assert mux.quiet_hours_start == time(23, 0)
        assert mux.quiet_hours_end == time(7, 0)
        assert mux.min_prazo_dias == 5


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


class TestCmdNotify:
    """cmd_notify dispatched via main() — covers the big subcommand body."""

    URGENT_EMAIL = (
        "De: projudisistema@tjpr.jus.br\n"
        "Data: 21/05/2026\n"
        "Processo 0001234-56.2026.8.16.0001\n"
        "Despacho: prazo de 2 dias uteis.\n"
    )
    NO_INTIMACAO_EMAIL = "Apenas um texto sem intimacao nem processo."

    def _write(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "email.txt"
        p.write_text(content, encoding="utf-8")
        return p

    def test_no_urgentes_exits_0(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        path = self._write(tmp_path, self.NO_INTIMACAO_EMAIL)
        rc = main(
            [
                "notify",
                "-i",
                str(path),
                "--chat-id",
                "5541999999999@s.whatsapp.net",
                "--dry-run",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert out["sent"] is False
        assert out["reason"] == "no_urgentes"

    def test_missing_chat_id_exits_2(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        path = self._write(tmp_path, self.URGENT_EMAIL)
        rc = main(
            [
                "notify",
                "-i",
                str(path),
                "--hoje",
                "2026-05-22",
                "--approved",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert rc == 2
        assert "chat_id" in out["error"]

    def test_notify_requires_approval_before_send(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        path = self._write(tmp_path, self.URGENT_EMAIL)
        rc = main(
            [
                "notify",
                "-i",
                str(path),
                "--chat-id",
                "5541999999999@s.whatsapp.net",
                "--hoje",
                "2026-05-22",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert out["sent"] is False
        assert out["reason"] == "requires_approval"
        assert "PRAZOS URGENTES" in out["message"]

    def test_dry_run_with_chat_id(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        path = self._write(tmp_path, self.URGENT_EMAIL)
        rc = main(
            [
                "notify",
                "-i",
                str(path),
                "--chat-id",
                "5541999999999@s.whatsapp.net",
                "--hoje",
                "2026-05-22",
                "--dry-run",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert out["sent"] is False
        assert out["dry_run"] is True

    def test_channels_missing_config_exits_2(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        path = self._write(tmp_path, self.URGENT_EMAIL)
        # email channel without smtp_host in config → ValueError → exit 2
        rc = main(
            [
                "notify",
                "-i",
                str(path),
                "--channels",
                "email",
                "--hoje",
                "2026-05-22",
                "--approved",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert rc == 2
        assert "error" in out

    def test_channels_dry_run(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        path = self._write(tmp_path, self.URGENT_EMAIL)
        rc = main(
            [
                "notify",
                "-i",
                str(path),
                "--chat-id",
                "5541999999999@s.whatsapp.net",
                "--channels",
                "whatsapp",
                "--hoje",
                "2026-05-22",
                "--dry-run",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert out["sent"] is False
        assert out["dry_run"] is True
        assert out["channels"] == ["whatsapp"]


class TestCmdHealthEntryPoint:
    """Exercita health pelo entry-point main() pra cobrir argparse wiring."""

    def test_main_health_json(self, capsys: pytest.CaptureFixture) -> None:
        rc = main(["health", "--format", "json"])
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert "status" in out
