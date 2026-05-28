"""Tests tjsp_parser — corpus 100% sintetico."""

from __future__ import annotations

from datetime import date

from legalops.tjsp_parser import Intimacao, ParseResult, parse_email


class TestBasic:
    def test_empty_text(self) -> None:
        r = parse_email("")
        assert r.total == 0
        assert "vazio" in r.erros[0].lower()

    def test_no_cnj(self) -> None:
        r = parse_email("Texto qualquer sem numero de processo.")
        assert r.total == 0
        assert any("CNJ" in e for e in r.erros)

    def test_returns_parse_result(self) -> None:
        r = parse_email("Autos nro 1000000-12.2026.8.26.0100 despacho.")
        assert isinstance(r, ParseResult)


class TestSingleProcess:
    def test_extract_cnj(self) -> None:
        txt = "Autos nro 1234567-89.2026.8.26.0100 — despacho de mero expediente."
        r = parse_email(txt)
        assert r.total == 1
        assert r.intimacoes[0].numero_processo == "1234567-89.2026.8.26.0100"

    def test_extract_tipo_despacho(self) -> None:
        r = parse_email("Processo 1234567-89.2026.8.26.0100\nDespacho: cumpra-se.")
        assert r.intimacoes[0].tipo_ato == "despacho"

    def test_extract_tipo_sentenca(self) -> None:
        r = parse_email("Processo 1234567-89.2026.8.26.0100\nSentença julgou procedente.")
        assert r.intimacoes[0].tipo_ato == "sentenca"

    def test_extract_tipo_intimacao(self) -> None:
        r = parse_email("Processo 1234567-89.2026.8.26.0100\nIntime-se a parte.")
        assert r.intimacoes[0].tipo_ato == "intimacao"


class TestVaraForo:
    def test_extract_vara_ordinal(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\n3ª Vara Cível"
        r = parse_email(txt)
        assert r.intimacoes[0].vara is not None
        assert "Vara" in r.intimacoes[0].vara

    def test_vara_with_foro(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\n2a Vara Civel\nForo Regional de Santo Amaro."
        r = parse_email(txt)
        assert r.intimacoes[0].vara is not None
        assert "Foro" in r.intimacoes[0].vara

    def test_comarca_fallback_foro(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nForo de São Paulo."
        r = parse_email(txt)
        assert r.intimacoes[0].comarca is not None

    def test_comarca_explicit(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nComarca de Campinas."
        r = parse_email(txt)
        assert r.intimacoes[0].comarca is not None
        assert "Campinas" in r.intimacoes[0].comarca


class TestPrazo:
    def test_prazo_simples(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nApresente em prazo de 15 dias."
        r = parse_email(txt)
        assert r.intimacoes[0].prazo_dias == 15

    def test_prazo_peremptorio(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nprazo peremptório de 10 dias."
        r = parse_email(txt)
        assert r.intimacoes[0].prazo_dias == 10

    def test_prazo_uteis(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nprazo de 30 dias uteis."
        r = parse_email(txt)
        assert r.intimacoes[0].prazo_dias == 30

    def test_sem_prazo(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nMero expediente."
        r = parse_email(txt)
        assert r.intimacoes[0].prazo_dias is None


class TestData:
    def test_data_ddmmyyyy(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nPublicado em 15/05/2026."
        r = parse_email(txt)
        assert r.intimacoes[0].data_publicacao == date(2026, 5, 15)

    def test_data_iso(self) -> None:
        txt = "Processo 1234567-89.2026.8.26.0100\nData: 2026-05-15."
        r = parse_email(txt)
        assert r.intimacoes[0].data_publicacao == date(2026, 5, 15)


class TestMultiProcess:
    def test_dois_processos(self) -> None:
        txt = (
            "Autos nro 1111111-11.2026.8.26.0100 despacho.\n"
            "---\n"
            "Autos nro 2222222-22.2026.8.26.0100 sentença."
        )
        r = parse_email(txt)
        assert r.total == 2

    def test_quatro_processos(self) -> None:
        txt = "\n".join(f"Autos nro {n}111111-11.2026.8.26.0100 despacho." for n in range(1, 5))
        r = parse_email(txt)
        assert r.total == 4


class TestStructure:
    def test_intimacao_frozen(self) -> None:
        r = parse_email("Processo 1234567-89.2026.8.26.0100 despacho.")
        assert isinstance(r.intimacoes[0], Intimacao)

    def test_trecho_relevante_nonempty(self) -> None:
        r = parse_email("Processo 1234567-89.2026.8.26.0100 despacho.")
        assert len(r.intimacoes[0].trecho_relevante) > 0
