"""Tests para os subcomandos-bridge v0.2 do CLI legalops.

Cobrem os modulos internos deterministicos expostos como subcomandos:
tribunal-detect, red-flags, pia, dpa, anpd, doc-template, doc-extract.

Dados SINTETICOS apenas — nenhum PII real (hook no-real-pii bloquearia).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from legalops.cli import main


def _run_cli(args, cwd):
    return subprocess.run(  # noqa: S603 - test helper invokes controlled CLI args
        [sys.executable, "-m", "legalops.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


class TestTribunalDetect:
    def test_detecta_via_input(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        # Arrange
        f = tmp_path / "email.txt"
        f.write_text("Tribunal de Justica do Parana Projudi", encoding="utf-8")
        # Act
        code = main(["tribunal-detect", "--input", str(f), "--sender", "x@tjpr.jus.br"])
        out = json.loads(capsys.readouterr().out)
        # Assert
        assert code == 0
        assert out["tribunal"] == "tjpr"


class TestRedFlags:
    def test_detecta_red_flags(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        f = tmp_path / "contrato.txt"
        f.write_text("Sem clausula de MAC. Indenizacao ilimitada.", encoding="utf-8")
        code = main(["red-flags", "--input", str(f)])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["count"] >= 1
        assert all("severidade" in fl for fl in out["flags"])

    def test_redige_pii(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        f = tmp_path / "c.txt"
        f.write_text("Contratante CPF 123.456.789-00. Sem cap de indenizacao.", encoding="utf-8")
        code = main(["red-flags", "--input", str(f)])
        raw = capsys.readouterr().out
        assert code == 0
        assert "123.456.789-00" not in raw


class TestPia:
    def test_avalia_ripd_sensivel(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "pia",
                "--tipo-operacao",
                "coleta",
                "--finalidade",
                "pesquisa clinica",
                "--base-legal",
                "consentimento",
                "--tipos-dados",
                "sensivel",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["operacao"] == "coleta"
        assert out["nivel"] in ("baixo", "medio", "alto", "critico")


class TestPiaExtra:
    def test_nao_necessario_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "pia",
                "--tipo-operacao",
                "compartilhamento",
                "--finalidade",
                "marketing",
                "--nao-necessario",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["operacao"] == "compartilhamento"


class TestDpa:
    def test_renderiza_dpa(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "dpa",
                "--controlador",
                "ACME",
                "--operador",
                "VENDOR",
                "--finalidade",
                "analytics",
                "--objeto",
                "tratamento de leads",
                "--categorias",
                "nome,email",
                "--prazo-retencao",
                "24 meses",
                "--suboperadores",
                "--transferencia-internacional",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert "ACORDO DE TRATAMENTO DE DADOS" in out["dpa"]
        assert "analytics" in out["dpa"]


class TestAnpd:
    def test_gera_plano_critico(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "anpd",
                "--descricao",
                "vazamento de base de dados",
                "--dados-afetados",
                "sensivel",
                "--num-titulares",
                "500",
                "--vazamento-confirmado",
                "--data-descoberta",
                "2026-06-01",
                "--hoje",
                "2026-06-02",
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["comunicar_anpd"] is True
        assert isinstance(out["passos"], list) and out["passos"]


class TestDocTemplate:
    def test_renderiza_procuracao(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "doc-template",
                "--template",
                "procuracao",
                "--vars",
                json.dumps(
                    {
                        "outorgante": "CLI-001",
                        "outorgado": "ADV-002",
                        "poderes": "ad_judicia",
                        "comarca": "Curitiba",
                    }
                ),
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert "PROCURACAO" in out["texto"]
        assert "CLI-001" in out["texto"]

    def test_vars_json_invalido(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["doc-template", "--template", "procuracao", "--vars", "{nao-json"])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "error" in out

    def test_renderiza_contrato_honorarios(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "doc-template",
                "--template",
                "contrato_honorarios",
                "--vars",
                json.dumps({"contratante": "CLI-001", "contratado": "ADV-002"}),
            ]
        )
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["template"] == "contrato_honorarios"
        assert out["texto"]


class TestDocExtract:
    def test_extrai_procuracao(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        f = tmp_path / "proc.txt"
        f.write_text(
            "PROCURACAO OUTORGANTE: CLI-001 OUTORGADO: ADV-002 OAB 12345 "
            "Comarca de Curitiba ad judicia",
            encoding="utf-8",
        )
        code = main(["doc-extract", "--input", str(f), "--kind", "procuracao"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["kind"] == "procuracao"
        assert "confianca" in out["campos"]

    def test_extrai_contrato_honorarios(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        f = tmp_path / "ch.txt"
        f.write_text(
            "CONTRATO DE HONORARIOS contratante CLI-001 contratado ADV-002 "
            "objeto acao revisional valor R$ 5.000,00 a vista",
            encoding="utf-8",
        )
        code = main(["doc-extract", "--input", str(f), "--kind", "contrato_honorarios"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["kind"] == "contrato_honorarios"
        assert "confianca" in out["campos"]


# ── v0.3 bridges ──────────────────────────────────────────────────────────

# CNPJ sintetico valido (digito verificador OK) — nao corresponde a empresa real.
_CNPJ_SINTETICO = "26715907000120"


class TestSocietario:
    def test_estrutura_coerente(self, capsys: pytest.CaptureFixture[str]) -> None:
        socios = json.dumps(
            [
                {"nome_alias": "SOCIO-A", "percentual": 60, "tipo": "quotista"},
                {"nome_alias": "SOCIO-B", "percentual": 40, "tipo": "administrador"},
            ]
        )
        code = main(["societario", "--socios", socios, "--tipo", "ltda"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["coerente"] is True
        assert out["problemas"] == []
        assert out["soma_participacoes"] == 100

    def test_cnpj_valido_aceito(self, capsys: pytest.CaptureFixture[str]) -> None:
        socios = json.dumps([{"nome_alias": "X", "percentual": 100}])
        code = main(["societario", "--socios", socios, "--tipo", "slu", "--cnpj", _CNPJ_SINTETICO])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert "CNPJ invalido (digito verificador)" not in out["problemas"]

    def test_soma_diferente_de_100_falha(self, capsys: pytest.CaptureFixture[str]) -> None:
        socios = json.dumps([{"nome_alias": "X", "percentual": 50}])
        code = main(["societario", "--socios", socios])
        out = json.loads(capsys.readouterr().out)
        assert code == 1
        assert out["coerente"] is False
        assert any("Soma" in p for p in out["problemas"])

    def test_json_invalido(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["societario", "--socios", "{nao json"])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "JSON invalido" in out["error"]

    def test_socios_nao_lista(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["societario", "--socios", '{"a": 1}'])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "lista JSON" in out["error"]

    def test_socio_nao_objeto(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["societario", "--socios", "[1, 2]"])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "objeto JSON" in out["error"]

    def test_tipo_socio_invalido(self, capsys: pytest.CaptureFixture[str]) -> None:
        socios = json.dumps([{"nome_alias": "X", "percentual": 100, "tipo": "fantasma"}])
        code = main(["societario", "--socios", socios])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "tipo invalido" in out["error"]

    def test_percentual_ausente(self, capsys: pytest.CaptureFixture[str]) -> None:
        socios = json.dumps([{"nome_alias": "X"}])
        code = main(["societario", "--socios", socios])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "percentual" in out["error"]


class TestVendorReview:
    def test_json_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["vendor-review"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["checklist"] == "vendor_ai_review_padrao"
        assert len(out["itens"]) == 10
        assert all({"chave", "artigo", "status"} <= set(it) for it in out["itens"])

    def test_text_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["vendor-review", "--format", "text"])
        out = capsys.readouterr().out
        assert code == 0
        assert "vendor_ai_review_padrao" in out
        assert "transferencia_internacional" in out


class TestDisclosure:
    def test_gap_detectado(self, capsys: pytest.CaptureFixture[str]) -> None:
        reps = json.dumps([{"id": "R-1", "texto": "rep um", "requer_schedule": True}])
        code = main(["disclosure", "--representacoes", reps])
        out = json.loads(capsys.readouterr().out)
        assert code == 1
        assert [g["id"] for g in out["gaps"]] == ["R-1"]

    def test_sem_gaps_nem_inconsistencias(self, capsys: pytest.CaptureFixture[str]) -> None:
        reps = json.dumps([{"id": "R-1", "requer_schedule": True}])
        sched = json.dumps([{"rep_id": "R-1", "conteudo": "divulgado"}])
        code = main(["disclosure", "--representacoes", reps, "--schedule", sched])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["gaps"] == []
        assert out["inconsistencias"] == []

    def test_inconsistencia_detectada(self, capsys: pytest.CaptureFixture[str]) -> None:
        reps = json.dumps([{"id": "R-1", "requer_schedule": False}])
        sched = json.dumps([{"rep_id": "R-99", "conteudo": "orfa"}])
        code = main(["disclosure", "--representacoes", reps, "--schedule", sched])
        out = json.loads(capsys.readouterr().out)
        assert code == 1
        assert [i["rep_id"] for i in out["inconsistencias"]] == ["R-99"]

    def test_reps_json_invalido(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["disclosure", "--representacoes", "{nao"])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "representacoes JSON invalido" in out["error"]

    def test_reps_nao_lista(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["disclosure", "--representacoes", '{"id": 1}'])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "lista JSON" in out["error"]

    def test_rep_sem_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["disclosure", "--representacoes", '[{"texto": "x"}]'])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "'id'" in out["error"]

    def test_schedule_json_invalido(self, capsys: pytest.CaptureFixture[str]) -> None:
        reps = json.dumps([{"id": "R-1", "requer_schedule": False}])
        code = main(["disclosure", "--representacoes", reps, "--schedule", "{nao"])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "schedule JSON invalido" in out["error"]

    def test_schedule_nao_lista(self, capsys: pytest.CaptureFixture[str]) -> None:
        reps = json.dumps([{"id": "R-1", "requer_schedule": False}])
        code = main(["disclosure", "--representacoes", reps, "--schedule", '{"rep_id": 1}'])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "lista JSON" in out["error"]

    def test_schedule_item_sem_rep_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        reps = json.dumps([{"id": "R-1", "requer_schedule": False}])
        code = main(["disclosure", "--representacoes", reps, "--schedule", '[{"conteudo": "x"}]'])
        out = json.loads(capsys.readouterr().out)
        assert code == 2
        assert "'rep_id'" in out["error"]


class TestDueDiligence:
    def test_checklist_completo(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["due-diligence"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["area_filtro"] is None
        assert out["n_itens"] == 13

    def test_filtro_por_area(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["due-diligence", "--area", "fiscal"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["area_filtro"] == "fiscal"
        assert all(it["area"] == "fiscal" for it in out["itens"])
        assert out["n_itens"] == 3


def test_validar_extracao_ok(tmp_path):
    extr = {
        "data_publicacao": "2026-07-01",
        "prazo_dias": 15,
        "parte": "particular",
        "tribunal": "TJPR",
        "via_dje": True,
        "confianca": 0.9,
        "cnj": "0001234-56.2026.8.16.0001",
        "ref": "PROC-1",
        "ato": "contestacao",
    }
    (tmp_path / "a.json").write_text(json.dumps(extr))
    (tmp_path / "b.json").write_text(json.dumps(extr))
    r = _run_cli(
        [
            "validar-extracao",
            "--file-a",
            "a.json",
            "--file-b",
            "b.json",
            "--hoje",
            "2026-07-09",
        ],
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["status"] == "ok"


def test_validar_extracao_divergencia_exit_3(tmp_path):
    a = {
        "data_publicacao": "2026-07-01",
        "prazo_dias": 15,
        "parte": "particular",
        "tribunal": "TJPR",
        "via_dje": True,
        "ref": "PROC-1",
        "ato": "contestacao",
    }
    b = dict(a, prazo_dias=30)
    (tmp_path / "a.json").write_text(json.dumps(a))
    (tmp_path / "b.json").write_text(json.dumps(b))
    r = _run_cli(
        [
            "validar-extracao",
            "--file-a",
            "a.json",
            "--file-b",
            "b.json",
            "--hoje",
            "2026-07-09",
        ],
        cwd=tmp_path,
    )
    assert r.returncode == 3
    out = json.loads(r.stdout)
    assert out["status"] == "revisao_manual_obrigatoria"
    assert out["reasons"]
