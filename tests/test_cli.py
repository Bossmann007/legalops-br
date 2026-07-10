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


class TestCmdContract:
    def test_contract_detecta_clausula_e_redige_pii(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Arrange
        f = tmp_path / "contrato.txt"
        f.write_text(
            "Contratante CPF 123.456.789-00. Havera capitalizacao mensal de juros.",
            encoding="utf-8",
        )
        # Act
        code = main(["contract", "--input", str(f)])
        out = json.loads(capsys.readouterr().out)
        # Assert
        assert code == 0
        assert "123.456.789-00" not in json.dumps(out)
        assert any(c["tipo"] == "juros_capitalizados" for c in out["clausulas"])

    def test_contract_skip_redact(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "contrato.txt"
        f.write_text("Contrato equilibrado de prestacao de servicos.", encoding="utf-8")
        code = main(["contract", "--input", str(f), "--skip-redact"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0 and out["nivel"] == "baixo"


class TestCmdDsar:
    def test_dsar_classifica_e_calcula_prazo(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "req.txt"
        f.write_text(
            "Solicito acesso aos meus dados pessoais (CPF 123.456.789-00).",
            encoding="utf-8",
        )
        code = main(
            ["dsar", "--input", str(f), "--recebimento", "2026-05-20", "--hoje", "2026-05-22"]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["codigo_direito"] == "acesso"
        assert out["prazo_final"] == "2026-06-04"
        assert "123.456.789-00" not in json.dumps(out)

    def test_dsar_direito_explicito(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "req.txt"
        f.write_text("texto generico sem palavra-chave", encoding="utf-8")
        code = main(["dsar", "--input", str(f), "--direito", "eliminacao"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["codigo_direito"] == "eliminacao"
        assert "Art. 19" not in out["referencia_prazo"]
        assert "Art. 19" not in out["texto_resposta"]

    def test_dsar_sem_classificacao_retorna_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "req.txt"
        f.write_text("xyz", encoding="utf-8")
        code = main(["dsar", "--input", str(f)])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "direitos" in out


class TestCmdPrazo:
    def test_prazo_simples_deterministico(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-05-21",
                "--prazo-dias",
                "5",
                "--hoje",
                "2026-05-22",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["data_final"] == "2026-05-28"
        assert out["dias_corridos"] == 7
        assert out["flags"]["dobro_aplicado"] is False

    def test_prazo_dobro_mp_via_dje(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-05-21",
                "--prazo-dias",
                "5",
                "--parte",
                "mp",
                "--via-dje",
                "--hoje",
                "2026-05-22",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["prazo_efetivo_dias"] == 10
        assert out["flags"]["dobro_aplicado"] is True
        assert out["data_intimacao_considerada"] == "2026-05-22"

    def test_prazo_recesso_forense(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-12-10",
                "--prazo-dias",
                "15",
                "--hoje",
                "2026-12-11",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["data_final"] > "2027-01-20"
        assert out["flags"]["recesso_aplicado"] is True

    def test_prazo_tjsp_sem_recesso_modelado_fail_soft(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-12-10",
                "--prazo-dias",
                "15",
                "--tribunal",
                "TJSP",
                "--hoje",
                "2026-12-11",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["tribunal"] == "TJSP"
        assert out["flags"]["recesso_aplicado"] is False
        assert "não modelado para TJSP" in out["aviso_tribunal"]

    def test_prazo_feriado_movel_corpus_christi(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-05-21",
                "--prazo-dias",
                "15",
                "--hoje",
                "2026-05-22",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["data_final"] == "2026-06-12"

    def test_prazo_salvar_e_prazos_listar(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-05-21",
                "--prazo-dias",
                "5",
                "--hoje",
                "2026-05-22",
                "--salvar",
                "--ref",
                "PROC-001",
                "--ato",
                "manifestacao",
            ]
        )
        saved = json.loads(capsys.readouterr().out)
        assert code == 0
        assert saved["salvo"] is True
        assert saved["prazo_registrado"]["ref"] == "PROC-001"

        code = main(["prazos", "--ate", "7", "--hoje", "2026-05-22"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["avisos"] == []
        assert [(p["ref"], p["data_final"], p["dias_ate"]) for p in out["prazos"]] == [
            ("PROC-001", "2026-05-28", 6)
        ]

    def test_prazo_salvar_exige_ref_e_ato(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-05-21",
                "--prazo-dias",
                "5",
                "--hoje",
                "2026-05-22",
                "--salvar",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert out["error"] == "--salvar exige --ref e --ato"

    def test_prazo_salvar_ledger_invalido_retorna_2(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "prazos.json").write_text("{}", encoding="utf-8")
        code = main(
            [
                "prazo",
                "--data-publicacao",
                "2026-05-21",
                "--prazo-dias",
                "5",
                "--hoje",
                "2026-05-22",
                "--salvar",
                "--ref",
                "PROC-001",
                "--ato",
                "manifestacao",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "prazos.json deve conter uma lista" in out["error"]

    def test_prazos_sem_ledger_retorna_lista_vazia(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        code = main(["prazos", "--hoje", "2026-05-22"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["prazos"] == []
        assert "data/prazos.json ausente" in out["avisos"][0]

    def test_prazos_ledger_com_item_invalido_retorna_2(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "prazos.json").write_text(json.dumps(["PROC-001"]), encoding="utf-8")
        code = main(["prazos", "--hoje", "2026-05-22"])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "cada prazo deve ser um objeto JSON" in out["error"]

    def test_prazos_filtra_janela_e_cumpridos(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "prazos.json").write_text(
            json.dumps(
                [
                    {
                        "ref": "PROC-001",
                        "ato": "manifestacao",
                        "data_final": "2026-05-23",
                        "tribunal": "TJPR",
                        "criado_em": "2026-05-20",
                        "status": "aberto",
                    },
                    {
                        "ref": "PROC-002",
                        "ato": "recurso",
                        "data_final": "2026-06-10",
                        "tribunal": "TJPR",
                        "criado_em": "2026-05-20",
                        "status": "aberto",
                    },
                    {
                        "ref": "PROC-003",
                        "ato": "juntada",
                        "data_final": "2026-05-24",
                        "tribunal": "TJPR",
                        "criado_em": "2026-05-20",
                        "status": "cumprido",
                    },
                    {
                        "ref": "PROC-004",
                        "ato": "sem data",
                        "tribunal": "TJPR",
                        "criado_em": "2026-05-20",
                        "status": "aberto",
                    },
                ]
            ),
            encoding="utf-8",
        )
        code = main(["prazos", "--ate", "7", "--hoje", "2026-05-22"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert [p["ref"] for p in out["prazos"]] == ["PROC-001"]

        code = main(["prazos", "--ate", "7", "--hoje", "2026-05-22", "--incluir-cumpridos"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert [p["ref"] for p in out["prazos"]] == ["PROC-001", "PROC-003"]


class TestCmdRenovacao:
    def test_renovacao_sem_arquivo_retorna_lista_vazia(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        code = main(["renovacao", "--hoje", "2026-05-20"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["alertas"] == []
        assert "data/contratos.json ausente" in out["avisos"][0]

    def test_renovacao_alertas_com_alias_sintetico(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "contratos.json").write_text(
            json.dumps(
                {
                    "contratos": [
                        {
                            "contrato_id": "CTR-001",
                            "alias": "CLI-001",
                            "data_inicio": "2026-01-01",
                            "data_fim": "2026-06-01",
                            "aviso_previo_dias": 15,
                            "renovacao_automatica": True,
                        },
                        {
                            "contrato_id": "CTR-002",
                            "alias": "CLI-002",
                            "data_inicio": "2026-01-01",
                            "data_fim": "2026-12-31",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        code = main(["renovacao", "--hoje", "2026-05-20"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert [a["contrato_id"] for a in out["alertas"]] == ["CTR-001"]
        assert out["alertas"][0]["alias"] == "CLI-001"
        assert out["alertas"][0]["urgencia"] == "vencido"

    def test_renovacao_incluir_ok(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "contratos.json").write_text(
            json.dumps(
                [
                    {
                        "contrato_id": "CTR-010",
                        "alias": "CLI-010",
                        "data_inicio": "2026-01-01",
                        "data_fim": "2026-12-31",
                    }
                ]
            ),
            encoding="utf-8",
        )
        code = main(["renovacao", "--hoje", "2026-05-20", "--incluir-ok"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["alertas"][0]["urgencia"] == "ok"


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

    def test_redact_strict_limpo_exit_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "pii.txt"
        f.write_text("CPF 123.456.789-00", encoding="utf-8")
        code = main(["redact", "--input", str(f), "--strict"])
        out = capsys.readouterr().out
        assert code == 0
        assert "123.456.789-00" not in out

    def test_redact_strict_residual_exit_3_sem_valor_cru(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "residual.txt"
        f.write_text("ID interno 12345678900 referencia X", encoding="utf-8")
        code = main(["redact", "--input", str(f), "--strict"])
        out = json.loads(capsys.readouterr().out)
        assert code == 3
        assert out["residual_pii"] == [{"tipo": "CPF_NUMERIC", "span": [11, 22]}]
        assert "12345678900" not in json.dumps(out)


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
