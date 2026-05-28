"""Tests para br_validators — CPF/CNPJ digit verifier."""

from __future__ import annotations

import pytest

from legalops.br_validators import _digits_only, is_valid_cnpj, is_valid_cpf


class TestCPFValid:
    @pytest.mark.parametrize(
        "cpf",
        [
            "12345678909",  # CPF matematicamente valido
            "123.456.789-09",  # formatado
            "529.982.247-25",  # outro valido
            "52998224725",
        ],
    )
    def test_valid_cpf(self, cpf: str) -> None:
        assert is_valid_cpf(cpf) is True


class TestCPFInvalid:
    @pytest.mark.parametrize(
        "cpf",
        [
            "",
            "1234",
            "12345678900",  # digito verificador errado
            "99999999999",  # todos iguais
            "00000000000",
            "11111111111",
            "abc.def.ghi-jk",
        ],
    )
    def test_invalid_cpf(self, cpf: str) -> None:
        assert is_valid_cpf(cpf) is False


class TestCNPJValid:
    @pytest.mark.parametrize(
        "cnpj",
        [
            "11222333000181",  # valido
            "11.222.333/0001-81",  # formatado
            "76.417.005/0001-86",  # Municipio Curitiba (publico)
        ],
    )
    def test_valid_cnpj(self, cnpj: str) -> None:
        assert is_valid_cnpj(cnpj) is True


class TestCNPJInvalid:
    @pytest.mark.parametrize(
        "cnpj",
        [
            "",
            "12345",
            "11222333000180",  # digito errado
            "00000000000000",  # todos iguais
            "99999999999999",
            "abc.def.ghi/jklm-no",
        ],
    )
    def test_invalid_cnpj(self, cnpj: str) -> None:
        assert is_valid_cnpj(cnpj) is False


class TestDigitsOnly:
    def test_strip_formatting(self) -> None:
        assert _digits_only("123.456.789-00") == "12345678900"

    def test_strip_letters(self) -> None:
        assert _digits_only("abc123def") == "123"

    def test_empty(self) -> None:
        assert _digits_only("") == ""
