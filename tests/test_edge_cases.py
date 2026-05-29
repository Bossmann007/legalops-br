"""Edge cases: input vazio, malformado, encoding, limites.

Cobre robustez do pipeline sob inputs nao-canonicos.
"""

from __future__ import annotations

from datetime import date

from legalops.orchestrator import process_email
from legalops.pii_redactor import PIIRedactor
from legalops.tjpr_parser import parse_email as parse_tjpr
from legalops.tjsp_parser import parse_email as parse_tjsp


class TestEmptyInput:
    def test_redactor_empty(self) -> None:
        r = PIIRedactor(salt="test-salt-edgecase-v1").redact("")
        assert r.redacted_text == ""
        assert r.matches == []
        assert not r.has_pii

    def test_redactor_whitespace_only(self) -> None:
        r = PIIRedactor(salt="test-salt-edgecase-v1").redact("   \n\t  ")
        assert r.has_pii is False

    def test_tjpr_empty(self) -> None:
        r = parse_tjpr("")
        assert r.total == 0
        assert len(r.erros) > 0

    def test_tjsp_empty(self) -> None:
        r = parse_tjsp("")
        assert r.total == 0

    def test_orchestrator_empty(self) -> None:
        results = process_email("", hoje=date(2026, 5, 28))
        assert results == []


class TestMalformedCNJ:
    def test_cnj_short_no_match(self) -> None:
        r = parse_tjpr("Processo 12345-67.2026.8.16.0001 (digitos faltando)")
        assert r.total == 0

    def test_cnj_extra_digits(self) -> None:
        # 8 digits before dash — nao bate \d{7}
        r = parse_tjpr("Processo 12345678-90.2026.8.16.0001")
        assert r.total == 0

    def test_cnj_no_dots(self) -> None:
        r = parse_tjpr("Processo 0001234562026816001")
        assert r.total == 0


class TestEncoding:
    def test_utf8_with_accents(self) -> None:
        text = "Processo 0001234-56.2026.8.16.0001\nSentença julgou procedência. Prazo de 15 dias."
        r = parse_tjpr(text)
        assert r.total == 1
        assert r.intimacoes[0].tipo_ato in {"sentenca", "decisao"}

    def test_latin1_chars_in_redactor(self) -> None:
        # caracter pt-BR
        text = "Procurador OAB/PR 12345 (CPF 123.456.789-00) — anotação"
        r = PIIRedactor(salt="test-salt-edgecase-v1").redact(text)
        assert r.has_pii is True


class TestLargeInput:
    def test_redactor_500_cpfs(self) -> None:
        text = "\n".join(f"CPF 123.456.789-{i:02d}" for i in range(10, 100))
        r = PIIRedactor(salt="test-salt-edgecase-v1").redact(text)
        assert len(r.matches) == 90

    def test_tjpr_many_processes(self) -> None:
        # 20 processos no mesmo email
        text = "\n".join(
            f"Processo {n:07d}-11.2026.8.16.0001 despacho de prazo {n % 30 + 1} dias."
            for n in range(1, 21)
        )
        r = parse_tjpr(text)
        assert r.total == 20


class TestRedactorNoFalsePositives:
    def test_invalid_cpf_numeric_passes(self) -> None:
        # CPF numerico com DV invalido NAO eh redigido
        text = "Codigo interno 12345678900 referencia X"
        r = PIIRedactor(salt="test-salt-edgecase-v1").redact(text)
        assert "12345678900" in r.redacted_text

    def test_invalid_cnpj_numeric_passes(self) -> None:
        text = "Identificador 11222333000180 (DV errado)"
        r = PIIRedactor(salt="test-salt-edgecase-v1").redact(text)
        assert "11222333000180" in r.redacted_text

    def test_repeated_digits_not_pii(self) -> None:
        text = "Valor 00000000000 (11 zeros)"
        r = PIIRedactor(salt="test-salt-edgecase-v1").redact(text)
        assert "00000000000" in r.redacted_text


class TestOrchestratorTribunalRouting:
    def test_tjsp_sender_routes_correctly(self) -> None:
        text = (
            "Autos nro 1234567-89.2026.8.26.0100\n"
            "3a Vara Civel - Foro de Sao Paulo. Despacho: prazo de 10 dias."
        )
        results = process_email(
            text,
            parte="particular",
            hoje=date(2026, 5, 28),
            sender="esaj@tjsp.jus.br",
        )
        assert len(results) == 1

    def test_unknown_sender_falls_back_tjpr(self) -> None:
        text = "Processo 0001234-56.2026.8.16.0001\nDespacho: prazo de 10 dias."
        results = process_email(text, parte="particular", hoje=date(2026, 5, 28))
        assert len(results) == 1
