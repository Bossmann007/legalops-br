"""Extracao de campos estruturados de documentos juridicos BR.

Extrai campos via regex de dois tipos de documento: procuracao (poderes) e
contrato de honorarios. Roda DEPOIS do pii_redactor — assume que o texto pode
ja conter placeholders. Nao loga texto bruto.

Uso:
    >>> from legalops.doc_extractor import extract_procuracao
    >>> txt = "Outorgante: ACME LTDA. Outorgado: Dr. Fulano, OAB/PR 12345."
    >>> r = extract_procuracao(txt)
    >>> r.oab
    'PR 12345'
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Literal

__all__ = [
    "ContratoHonorariosCampos",
    "FormaPagamento",
    "Poderes",
    "ProcuracaoCampos",
    "extract_contrato_honorarios",
    "extract_procuracao",
]

Poderes = Literal[
    "ad_judicia",
    "ad_judicia_et_extra",
    "especiais",
    "desconhecido",
]

FormaPagamento = Literal[
    "a_vista",
    "parcelado",
    "exito",
    "misto",
    "desconhecido",
]

# Campos esperados para calculo de confianca (fracao encontrada).
_PROCURACAO_ESPERADOS: tuple[str, ...] = (
    "outorgante",
    "outorgado",
    "poderes",
    "comarca",
    "data",
)
_CONTRATO_ESPERADOS: tuple[str, ...] = (
    "contratante",
    "contratado",
    "objeto",
    "valor",
    "forma_pagamento",
    "foro_eleicao",
)

# Datas (reaproveita convencao do tjpr_parser).
DATE_DDMMYYYY_RE = re.compile(r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b")
DATE_YYYYMMDD_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

# Procuracao.
OUTORGANTE_RE = re.compile(
    r"outorgante[s]?\s*[:\-]?\s*([^\n,;]+?)(?:[,;\n]|outorgad|$)",
    re.IGNORECASE,
)
OUTORGADO_RE = re.compile(
    r"outorgad[oa][s]?\s*[:\-]?\s*([^\n,;]+?)(?:[,;\n]|OAB|inscrit|$)",
    re.IGNORECASE,
)
OAB_RE = re.compile(
    r"OAB[/\s]*([A-Z]{2})?\s*(?:n[ºo°.]*\s*)?(\d{1,6})",
    re.IGNORECASE,
)
COMARCA_RE = re.compile(
    r"comarca\s+(?:de\s+)?([\wÀ-ÿ\s\-]+?)(?:[.,;\n]|$)",
    re.IGNORECASE,
)

AD_JUDICIA_ET_EXTRA_RE = re.compile(
    r"ad[\-\s]?judicia\b[^.\n]*?et[\-\s]?extra",
    re.IGNORECASE,
)
AD_JUDICIA_RE = re.compile(r"ad[\-\s]?judicia\b", re.IGNORECASE)
PODERES_ESPECIAIS_RE = re.compile(
    r"poderes\s+especiais|\balienar\b|\btransigir\b|receber\s+e\s+dar\s+quita[çc][ãa]o",
    re.IGNORECASE,
)

# Contrato de honorarios.
CONTRATANTE_RE = re.compile(
    r"contratante\s*[:\-]?\s*([^\n,;]+?)(?:[,;\n]|contratad|$)",
    re.IGNORECASE,
)
CONTRATADO_RE = re.compile(
    r"contratad[oa]\s*[:\-]?\s*([^\n,;]+?)(?:[,;\n]|OAB|$)",
    re.IGNORECASE,
)
OBJETO_RE = re.compile(
    r"objeto\s*[:\-]?\s*([^\n]+?)(?:[.;\n]|$)",
    re.IGNORECASE,
)
VALOR_RE = re.compile(
    r"R\$\s*([\d.]+(?:,\d{2})?)",
    re.IGNORECASE,
)
PERCENTUAL_RE = re.compile(r"(\d{1,3})\s*%")
FORO_ELEICAO_RE = re.compile(
    r"foro\s*[:\-]?\s*(?:eleito\s+)?(?:da\s+)?(?:comarca\s+)?(?:de\s+)?([\wÀ-ÿ\s\-]+?)(?:[.,;\n]|$)",
    re.IGNORECASE,
)

PARCELADO_RE = re.compile(r"\bparcela[ds]?\b|\bparcelamento\b", re.IGNORECASE)
A_VISTA_RE = re.compile(r"[àa]\s*vista", re.IGNORECASE)
EXITO_RE = re.compile(r"\b[êe]xito\b|honor[áa]rios?\s+de\s+[êe]xito", re.IGNORECASE)


@dataclass(frozen=True)
class ProcuracaoCampos:
    """Campos extraidos de uma procuracao."""

    outorgante: str | None = None
    outorgado: str | None = None
    oab: str | None = None
    poderes: Poderes = "desconhecido"
    comarca: str | None = None
    data: date | None = None
    campos_ausentes: tuple[str, ...] = ()
    confianca: float = 0.0


@dataclass(frozen=True)
class ContratoHonorariosCampos:
    """Campos extraidos de um contrato de honorarios."""

    contratante: str | None = None
    contratado: str | None = None
    objeto: str | None = None
    valor: float | None = None
    percentual: int | None = None
    forma_pagamento: FormaPagamento = "desconhecido"
    foro_eleicao: str | None = None
    campos_ausentes: tuple[str, ...] = ()
    confianca: float = 0.0


def _parse_date_first(text: str) -> date | None:
    m = DATE_YYYYMMDD_RE.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = DATE_DDMMYYYY_RE.search(text)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    return None


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip(" \t.,;:-")
    return cleaned or None


def _match_group(pattern: re.Pattern[str], text: str, group: int = 1) -> str | None:
    m = pattern.search(text)
    if m:
        return _clean(m.group(group))
    return None


def _extract_oab(text: str) -> str | None:
    m = OAB_RE.search(text)
    if not m:
        return None
    uf = m.group(1)
    num = m.group(2)
    if uf:
        return f"{uf.upper()} {num}"
    return num


def _detect_poderes(text: str) -> Poderes:
    if AD_JUDICIA_ET_EXTRA_RE.search(text):
        return "ad_judicia_et_extra"
    if PODERES_ESPECIAIS_RE.search(text):
        return "especiais"
    if AD_JUDICIA_RE.search(text):
        return "ad_judicia"
    return "desconhecido"


def _parse_valor(text: str) -> float | None:
    m = VALOR_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    # Formato BR: "1.234,56" -> "1234.56".
    normalized = raw.replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _parse_percentual(text: str) -> int | None:
    m = PERCENTUAL_RE.search(text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _detect_forma_pagamento(text: str) -> FormaPagamento:
    has_exito = bool(EXITO_RE.search(text))
    has_parcelado = bool(PARCELADO_RE.search(text))
    has_vista = bool(A_VISTA_RE.search(text))

    sinais = sum((has_exito, has_parcelado, has_vista))
    if sinais >= 2:
        return "misto"
    if has_exito:
        return "exito"
    if has_parcelado:
        return "parcelado"
    if has_vista:
        return "a_vista"
    return "desconhecido"


def _compute(found: dict[str, bool], esperados: tuple[str, ...]) -> tuple[tuple[str, ...], float]:
    ausentes = tuple(c for c in esperados if not found.get(c, False))
    confianca = (len(esperados) - len(ausentes)) / len(esperados)
    return ausentes, confianca


def extract_procuracao(text: str) -> ProcuracaoCampos:
    """Extrai campos de uma procuracao a partir de texto livre.

    Args:
        text: Texto da procuracao (possivelmente com placeholders de PII).

    Returns:
        ``ProcuracaoCampos`` com campos encontrados, lista de campos ausentes e
        confianca (fracao 0..1 de campos esperados encontrados). Entrada vazia
        retorna objeto com confianca 0.
    """
    if not text or not text.strip():
        ausentes, confianca = _compute({}, _PROCURACAO_ESPERADOS)
        return ProcuracaoCampos(campos_ausentes=ausentes, confianca=confianca)

    outorgante = _match_group(OUTORGANTE_RE, text)
    outorgado = _match_group(OUTORGADO_RE, text)
    oab = _extract_oab(text)
    poderes = _detect_poderes(text)
    comarca = _match_group(COMARCA_RE, text)
    data = _parse_date_first(text)

    found = {
        "outorgante": outorgante is not None,
        "outorgado": outorgado is not None,
        "poderes": poderes != "desconhecido",
        "comarca": comarca is not None,
        "data": data is not None,
    }
    ausentes, confianca = _compute(found, _PROCURACAO_ESPERADOS)

    return ProcuracaoCampos(
        outorgante=outorgante,
        outorgado=outorgado,
        oab=oab,
        poderes=poderes,
        comarca=comarca,
        data=data,
        campos_ausentes=ausentes,
        confianca=confianca,
    )


def extract_contrato_honorarios(text: str) -> ContratoHonorariosCampos:
    """Extrai campos de um contrato de honorarios a partir de texto livre.

    Args:
        text: Texto do contrato (possivelmente com placeholders de PII).

    Returns:
        ``ContratoHonorariosCampos`` com campos encontrados, campos ausentes e
        confianca (fracao 0..1). Entrada vazia retorna objeto com confianca 0.
    """
    if not text or not text.strip():
        ausentes, confianca = _compute({}, _CONTRATO_ESPERADOS)
        return ContratoHonorariosCampos(campos_ausentes=ausentes, confianca=confianca)

    contratante = _match_group(CONTRATANTE_RE, text)
    contratado = _match_group(CONTRATADO_RE, text)
    objeto = _match_group(OBJETO_RE, text)
    valor = _parse_valor(text)
    percentual = _parse_percentual(text)
    forma_pagamento = _detect_forma_pagamento(text)
    foro_eleicao = _match_group(FORO_ELEICAO_RE, text)

    found = {
        "contratante": contratante is not None,
        "contratado": contratado is not None,
        "objeto": objeto is not None,
        "valor": valor is not None,
        "forma_pagamento": forma_pagamento != "desconhecido",
        "foro_eleicao": foro_eleicao is not None,
    }
    ausentes, confianca = _compute(found, _CONTRATO_ESPERADOS)

    return ContratoHonorariosCampos(
        contratante=contratante,
        contratado=contratado,
        objeto=objeto,
        valor=valor,
        percentual=percentual,
        forma_pagamento=forma_pagamento,
        foro_eleicao=foro_eleicao,
        campos_ausentes=ausentes,
        confianca=confianca,
    )
