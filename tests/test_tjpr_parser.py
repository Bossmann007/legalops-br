"""Tests para tjpr_parser — emails sinteticos, sem dados reais."""

from __future__ import annotations

from datetime import date

from legalops.tjpr_parser import (
    CNJ_RE,
    Intimacao,
    ParseResult,
    parse_email,
)


class TestCNJRegex:
    def test_valid_cnj_match(self) -> None:
        assert CNJ_RE.search("Processo 0001234-56.2026.8.16.0001 ajuizado")

    def test_invalid_format(self) -> None:
        assert not CNJ_RE.search("Processo 123-456")


class TestParseVazio:
    def test_texto_vazio(self) -> None:
        result = parse_email("")
        assert result.total == 0
        assert "vazio" in " ".join(result.erros).lower()

    def test_sem_processo(self) -> None:
        result = parse_email("Email comum sem numero processo")
        assert result.total == 0
        assert any("CNJ" in e for e in result.erros)


class TestParseUmaIntimacao:
    def test_extrai_numero_processo(self) -> None:
        txt = "Processo 0001234-56.2026.8.16.0001 - intimacao despacho"
        result = parse_email(txt)
        assert result.total == 1
        assert result.intimacoes[0].numero_processo == "0001234-56.2026.8.16.0001"

    def test_detecta_despacho(self) -> None:
        txt = "Processo 0001234-56.2026.8.16.0001\nDespacho: Intime-se."
        result = parse_email(txt)
        assert result.intimacoes[0].tipo_ato == "despacho"

    def test_detecta_sentenca(self) -> None:
        txt = "Processo 0001234-56.2026.8.16.0001\nSentenca: julgo procedente."
        result = parse_email(txt)
        assert result.intimacoes[0].tipo_ato == "sentenca"

    def test_detecta_decisao(self) -> None:
        txt = "Processo 0001234-56.2026.8.16.0001\nDecisao interlocutoria."
        result = parse_email(txt)
        assert result.intimacoes[0].tipo_ato == "decisao"

    def test_extrai_prazo_dias(self) -> None:
        txt = (
            "Processo 0001234-56.2026.8.16.0001\n"
            "Despacho: Intime-se para contestar no prazo de 15 dias uteis."
        )
        result = parse_email(txt)
        assert result.intimacoes[0].prazo_dias == 15
        assert "15" in (result.intimacoes[0].prazo_textual or "")

    def test_extrai_data_ddmmyyyy(self) -> None:
        txt = "Data: 21/05/2026\nProcesso 0001234-56.2026.8.16.0001\nDespacho."
        result = parse_email(txt)
        assert result.intimacoes[0].data_publicacao == date(2026, 5, 21)

    def test_extrai_data_yyyymmdd(self) -> None:
        txt = "Data: 2026-05-21\nProcesso 0001234-56.2026.8.16.0001\nDespacho."
        result = parse_email(txt)
        assert result.intimacoes[0].data_publicacao == date(2026, 5, 21)


class TestParseMultiplas:
    def test_multiplos_processos(self) -> None:
        txt = (
            "Processo 0001234-56.2026.8.16.0001\n"
            "Despacho: prazo de 15 dias.\n"
            "===\n"
            "Processo 0007890-12.2026.8.16.0002\n"
            "Sentenca: julgo procedente."
        )
        result = parse_email(txt)
        assert result.total == 2
        assert result.intimacoes[0].numero_processo == "0001234-56.2026.8.16.0001"
        assert result.intimacoes[1].numero_processo == "0007890-12.2026.8.16.0002"

    def test_tipos_diferentes_por_bloco(self) -> None:
        txt = (
            "Processo 0001234-56.2026.8.16.0001\n"
            "Despacho.\n"
            "Processo 0007890-12.2026.8.16.0002\n"
            "Sentenca."
        )
        result = parse_email(txt)
        assert result.intimacoes[0].tipo_ato == "despacho"
        assert result.intimacoes[1].tipo_ato == "sentenca"


class TestVaraComarca:
    def test_extrai_comarca(self) -> None:
        txt = (
            "Comarca de Curitiba.\n"
            "Processo 0001234-56.2026.8.16.0001\n"
            "Despacho."
        )
        result = parse_email(txt)
        assert result.intimacoes[0].comarca is not None
        assert "Curitiba" in result.intimacoes[0].comarca


class TestStructure:
    def test_returns_parse_result(self) -> None:
        result = parse_email("Processo 0001234-56.2026.8.16.0001")
        assert isinstance(result, ParseResult)

    def test_intimacao_is_dataclass(self) -> None:
        result = parse_email("Processo 0001234-56.2026.8.16.0001")
        assert isinstance(result.intimacoes[0], Intimacao)

    def test_trecho_relevante_truncado(self) -> None:
        long_text = "Processo 0001234-56.2026.8.16.0001 " + "x" * 500
        result = parse_email(long_text)
        assert len(result.intimacoes[0].trecho_relevante) <= 200


class TestIntegracaoPiiRedactor:
    def test_funciona_apos_redaction(self) -> None:
        """Texto ja redacted — placeholders [CPF_xxx] nao quebram parser."""
        txt = (
            "Email do TJPR\n"
            "Data: 21/05/2026\n"
            "Comarca de Curitiba\n"
            "Processo 0001234-56.2026.8.16.0001\n"
            "Cliente [CPF_a3f5b2], procurador [OAB_REDACTED]\n"
            "Despacho: prazo de 15 dias."
        )
        result = parse_email(txt)
        assert result.total == 1
        assert result.intimacoes[0].tipo_ato == "despacho"
        assert result.intimacoes[0].prazo_dias == 15
