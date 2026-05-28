"""Validadores de documentos BR via digito verificador.

Algoritmo modulo 11 oficial Receita Federal para CPF (11 digitos) e CNPJ
(14 digitos). Usado pelo pii_redactor pra reduzir falso positivo em
patterns numericos (CPF/CNPJ sem mascara) — G1 do docs/PII_GAPS.md.

Uso:
    >>> from legalops.br_validators import is_valid_cpf, is_valid_cnpj
    >>> is_valid_cpf("12345678909")
    True
    >>> is_valid_cpf("11111111111")
    False
"""

from __future__ import annotations


def _digits_only(s: str) -> str:
    """Remove tudo que nao for digito."""
    return "".join(c for c in s if c.isdigit())


def is_valid_cpf(value: str) -> bool:
    """Valida CPF via digito verificador (modulo 11).

    Aceita CPF formatado (`123.456.789-09`) ou apenas digitos (`12345678909`).
    Rejeita sequencias com todos digitos iguais (`11111111111`) — sao
    matematicamente validas mas reservadas/invalidas pela Receita.
    """
    digits = _digits_only(value)
    if len(digits) != 11:
        return False
    if len(set(digits)) == 1:
        return False

    nums = [int(d) for d in digits]

    # Digito 1: soma dos 9 primeiros * (10..2)
    soma1 = sum(nums[i] * (10 - i) for i in range(9))
    resto1 = (soma1 * 10) % 11
    dv1 = 0 if resto1 == 10 else resto1
    if dv1 != nums[9]:
        return False

    # Digito 2: soma dos 10 primeiros * (11..2)
    soma2 = sum(nums[i] * (11 - i) for i in range(10))
    resto2 = (soma2 * 10) % 11
    dv2 = 0 if resto2 == 10 else resto2
    return dv2 == nums[10]


def is_valid_cnpj(value: str) -> bool:
    """Valida CNPJ via digito verificador (modulo 11).

    Aceita CNPJ formatado (`12.345.678/0001-90`) ou apenas digitos.
    Rejeita sequencias com todos digitos iguais.
    """
    digits = _digits_only(value)
    if len(digits) != 14:
        return False
    if len(set(digits)) == 1:
        return False

    nums = [int(d) for d in digits]

    # Digito 1: pesos 5,4,3,2,9,8,7,6,5,4,3,2
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma1 = sum(nums[i] * pesos1[i] for i in range(12))
    resto1 = soma1 % 11
    dv1 = 0 if resto1 < 2 else 11 - resto1
    if dv1 != nums[12]:
        return False

    # Digito 2: pesos 6,5,4,3,2,9,8,7,6,5,4,3,2
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma2 = sum(nums[i] * pesos2[i] for i in range(13))
    resto2 = soma2 % 11
    dv2 = 0 if resto2 < 2 else 11 - resto2
    return dv2 == nums[13]
