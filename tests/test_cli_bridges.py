"""Tests para os subcomandos-bridge v0.2 do CLI legalops.

Cobrem os modulos internos deterministicos expostos como subcomandos:
tribunal-detect, red-flags, pia, dpa, anpd, doc-template, doc-extract.

Dados SINTETICOS apenas — nenhum PII real (hook no-real-pii bloquearia).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from legalops.cli import main


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
