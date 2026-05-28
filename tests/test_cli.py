"""Tests para CLI legalops."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from legalops.cli import build_parser, main

EMAIL_SAMPLE = (
    "De: projudisistema@tjpr.jus.br\n"
    "Data: 21/05/2026\n"
    "Processo 0001234-56.2026.8.16.0001\n"
    "Procurador OAB/PR 12345 (CPF 123.456.789-00)\n"
    "Despacho: prazo de 15 dias uteis.\n"
)


@pytest.fixture
def email_file(tmp_path: Path) -> Path:
    f = tmp_path / "email.txt"
    f.write_text(EMAIL_SAMPLE, encoding="utf-8")
    return f


class TestParserBuild:
    def test_builds_without_error(self) -> None:
        parser = build_parser()
        assert parser.prog == "legalops"

    def test_subcommands_exist(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["redact", "--input", "x"])
        assert args.cmd == "redact"


class TestCmdRedact:
    def test_redact_strips_cpf(self, email_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["redact", "--input", str(email_file)])
        assert code == 0
        out = capsys.readouterr().out
        assert "123.456.789-00" not in out
        assert "0001234-56.2026.8.16.0001" in out

    def test_redact_json_output(self, email_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["redact", "--input", str(email_file), "--json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert "redacted_text" in data
        assert "matches" in data
        assert data["matches"] >= 2


class TestCmdParse:
    def test_parse_finds_processo(
        self, email_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(["parse", "--input", str(email_file)])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["total"] == 1
        assert data["intimacoes"][0]["numero_processo"] == "0001234-56.2026.8.16.0001"

    def test_parse_extrai_prazo(self, email_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["parse", "--input", str(email_file)]) == 0
        data = json.loads(capsys.readouterr().out)
        assert data["intimacoes"][0]["prazo_dias"] == 15


class TestCmdPipeline:
    def test_pipeline_basico(self, email_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["pipeline", "--input", str(email_file), "--hoje", "2026-05-22"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["count"] == 1
        r = data["results"][0]
        assert r["numero_processo"] == "0001234-56.2026.8.16.0001"
        assert r["pii_matches"] >= 2
        assert r["calc"]["dies_a_quo"] == "2026-05-22"
        assert r["calc"]["prazo_efetivo_dias"] == 15

    def test_pipeline_fazenda_dobro(
        self, email_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(
            [
                "pipeline",
                "--input",
                str(email_file),
                "--parte",
                "fazenda",
                "--hoje",
                "2026-05-22",
            ]
        )
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["results"][0]["calc"]["prazo_efetivo_dias"] == 30

    def test_pipeline_via_dje(self, email_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "pipeline",
                "--input",
                str(email_file),
                "--via-dje",
                "--hoje",
                "2026-05-22",
            ]
        )
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["results"][0]["calc"]["dies_a_quo"] == "2026-05-25"

    def test_pipeline_audit_db(
        self,
        email_file: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        db = tmp_path / "audit.db"
        code = main(
            [
                "pipeline",
                "--input",
                str(email_file),
                "--audit-db",
                str(db),
                "--hoje",
                "2026-05-22",
            ]
        )
        assert code == 0
        assert db.exists()
        data = json.loads(capsys.readouterr().out)
        assert data["results"][0]["audit_seq"] is not None


class TestCmdAudit:
    def test_audit_verify_empty_db(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        db = tmp_path / "empty.db"
        code = main(["audit", "verify", "--db", str(db)])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["valid"] is True
        assert data["entries"] == 0

    def test_audit_verify_after_pipeline(
        self,
        email_file: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        db = tmp_path / "audit.db"
        main(
            [
                "pipeline",
                "--input",
                str(email_file),
                "--audit-db",
                str(db),
                "--hoje",
                "2026-05-22",
            ]
        )
        capsys.readouterr()
        code = main(["audit", "verify", "--db", str(db)])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["valid"] is True
        assert data["entries"] >= 3

    def test_audit_list(
        self,
        email_file: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        db = tmp_path / "audit.db"
        main(
            [
                "pipeline",
                "--input",
                str(email_file),
                "--audit-db",
                str(db),
                "--hoje",
                "2026-05-22",
            ]
        )
        capsys.readouterr()
        code = main(["audit", "list", "--db", str(db)])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        assert len(data) >= 3
        assert all("seq" in e for e in data)
        assert all(e["entry_hash"].endswith("...") for e in data)


class TestCmdBatch:
    @pytest.fixture
    def eml_dir(self, tmp_path: Path) -> Path:
        d = tmp_path / "inbox"
        d.mkdir()
        (d / "a.eml").write_bytes(
            b"From: projudisistema@tjpr.jus.br\n"
            b"Subject: Test 1\n"
            b"Date: Thu, 21 May 2026 10:00:00 -0300\n"
            b"Content-Type: text/plain; charset=utf-8\n\n"
            b"Processo 0001234-56.2026.8.16.0001\n"
            b"Despacho: prazo de 15 dias uteis.\n"
        )
        (d / "b.eml").write_bytes(
            b"From: projudisistema@tjpr.jus.br\n"
            b"Subject: Test 2\n"
            b"Date: Fri, 22 May 2026 10:00:00 -0300\n"
            b"Content-Type: text/plain; charset=utf-8\n\n"
            b"Processo 0009999-22.2026.8.16.0002\n"
            b"Despacho: prazo de 10 dias.\n"
        )
        return d

    def test_batch_processa_dois_emails(
        self, eml_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(["batch", "--dir", str(eml_dir), "--hoje", "2026-05-23"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["n_emails"] == 2
        assert data["n_intimacoes"] == 2

    def test_batch_extrai_processos(
        self, eml_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(["batch", "--dir", str(eml_dir), "--hoje", "2026-05-23"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        numeros = {p["numero_processo"] for r in data["results"] for p in r["processed"]}
        assert "0001234-56.2026.8.16.0001" in numeros
        assert "0009999-22.2026.8.16.0002" in numeros

    def test_batch_audit_db(
        self,
        eml_dir: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        db = tmp_path / "audit.db"
        code = main(
            [
                "batch",
                "--dir",
                str(eml_dir),
                "--audit-db",
                str(db),
                "--hoje",
                "2026-05-23",
            ]
        )
        assert code == 0
        assert db.exists()
        capsys.readouterr()
        code = main(["audit", "verify", "--db", str(db)])
        assert code == 0
        verify = json.loads(capsys.readouterr().out)
        assert verify["valid"] is True
        assert verify["entries"] >= 6

    def test_batch_dir_vazio_retorna_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        d = tmp_path / "empty"
        d.mkdir()
        code = main(["batch", "--dir", str(d)])
        assert code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["n_emails"] == 0


class TestStdin:
    def test_redact_from_stdin(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO("CPF 123.456.789-00 teste"))
        code = main(["redact"])
        assert code == 0
        out = capsys.readouterr().out
        assert "123.456.789-00" not in out
