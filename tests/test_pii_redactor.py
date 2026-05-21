"""Unit tests para PIIRedactor — corpus 100% sintetico, sem PII real."""

from __future__ import annotations

import pytest

from legalops.pii_redactor import PIIRedactor, RedactionResult


@pytest.fixture
def redactor() -> PIIRedactor:
    return PIIRedactor(salt="test-salt-v1")


class TestCPF:
    def test_redacts_formatted_cpf(self, redactor: PIIRedactor) -> None:
        text = "Cliente CPF 123.456.789-00 ajuizou acao"
        result = redactor.redact(text)
        assert "123.456.789-00" not in result.redacted_text
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == "CPF"

    def test_placeholder_deterministic(self, redactor: PIIRedactor) -> None:
        a = redactor.redact("CPF 111.222.333-44")
        b = redactor.redact("CPF 111.222.333-44")
        assert a.redacted_text == b.redacted_text


class TestCNPJ:
    def test_redacts_cnpj(self, redactor: PIIRedactor) -> None:
        text = "Empresa CNPJ 12.345.678/0001-90 contratou"
        result = redactor.redact(text)
        assert "12.345.678/0001-90" not in result.redacted_text
        assert any(m.pii_type == "CNPJ" for m in result.matches)


class TestOAB:
    def test_redacts_oab_slash(self, redactor: PIIRedactor) -> None:
        text = "Procurador OAB/PR 12345 subscreve"
        result = redactor.redact(text)
        assert "OAB/PR 12345" not in result.redacted_text

    def test_redacts_oab_dash(self, redactor: PIIRedactor) -> None:
        text = "Patrono OAB-SP 98765"
        result = redactor.redact(text)
        assert "OAB-SP 98765" not in result.redacted_text


class TestEmail:
    def test_redacts_email(self, redactor: PIIRedactor) -> None:
        text = "Contato: joao.silva@escritorio.test.local"
        result = redactor.redact(text)
        assert "joao.silva@escritorio.test.local" not in result.redacted_text


class TestPIXUUID:
    def test_redacts_uuid(self, redactor: PIIRedactor) -> None:
        text = "Chave PIX: 550e8400-e29b-41d4-a716-446655440000"
        result = redactor.redact(text)
        assert "550e8400-e29b-41d4-a716-446655440000" not in result.redacted_text


class TestMultiple:
    def test_multiple_in_one_doc(self, redactor: PIIRedactor) -> None:
        text = (
            "Procurador OAB/PR 12345, em nome do cliente CPF 123.456.789-00, "
            "comunica que a empresa CNPJ 12.345.678/0001-90 quitou via email "
            "para email@test.local"
        )
        result = redactor.redact(text)
        assert "123.456.789-00" not in result.redacted_text
        assert "12.345.678/0001-90" not in result.redacted_text
        assert "email@test.local" not in result.redacted_text
        assert len(result.matches) >= 4

    def test_clean_text_unchanged(self, redactor: PIIRedactor) -> None:
        text = "Este documento nao contem dados pessoais."
        result = redactor.redact(text)
        assert result.redacted_text == text
        assert result.has_pii is False


class TestStructure:
    def test_returns_redaction_result(self, redactor: PIIRedactor) -> None:
        result = redactor.redact("CPF 000.000.000-00")
        assert isinstance(result, RedactionResult)

    def test_match_has_full_sha256(self, redactor: PIIRedactor) -> None:
        result = redactor.redact("CPF 111.222.333-44")
        assert len(result.matches[0].sha256) == 64

    def test_match_span_valid(self, redactor: PIIRedactor) -> None:
        text = "CPF 111.222.333-44"
        result = redactor.redact(text)
        m = result.matches[0]
        assert text[m.span[0] : m.span[1]] == "111.222.333-44"
