"""Tests smoke pra tjsc_parser e tjrj_parser (reusam engine TJSP)."""

from __future__ import annotations

from datetime import date

from legalops.orchestrator import process_email
from legalops.tjrj_parser import parse_email as parse_tjrj
from legalops.tjsc_parser import parse_email as parse_tjsc


class TestTJSC:
    def test_basic_parse(self) -> None:
        txt = "e-Proc TJSC\nAutos nro 1234567-89.2026.8.24.0001\nDespacho: prazo de 15 dias."
        r = parse_tjsc(txt)
        assert r.total == 1
        assert r.intimacoes[0].prazo_dias == 15

    def test_orchestrator_routes_tjsc(self) -> None:
        txt = "e-Proc TJSC\nAutos nro 1234567-89.2026.8.24.0001\nDespacho: prazo de 10 dias."
        results = process_email(
            txt,
            parte="particular",
            hoje=date(2026, 5, 28),
            sender="eproc@tjsc.jus.br",
        )
        assert len(results) == 1


class TestTJRJ:
    def test_basic_parse(self) -> None:
        txt = (
            "PJe-RJ\nAutos nro 1234567-89.2026.8.19.0001\nSentenca: prazo de 15 dias para apelacao."
        )
        r = parse_tjrj(txt)
        assert r.total == 1

    def test_orchestrator_routes_tjrj(self) -> None:
        txt = (
            "PJe-RJ Tribunal de Justica do Rio de Janeiro\n"
            "Processo nro 1234567-89.2026.8.19.0001\n"
            "Decisao: prazo de 5 dias."
        )
        results = process_email(
            txt,
            parte="particular",
            hoje=date(2026, 5, 28),
            sender="pje@tjrj.jus.br",
        )
        assert len(results) == 1
