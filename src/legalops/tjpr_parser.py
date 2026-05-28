"""Parser de emails do TJPR/Projudi.

Extrai intimacoes estruturadas de emails encaminhados pelo sistema Projudi.
Roda DEPOIS do pii-redactor-br — assume que texto ja esta sem PII bruto.

Uso:
    >>> from legalops.tjpr_parser import parse_email
    >>> txt = "Processo 0001234-56.2026.8.16.0001\\nDespacho: prazo de 15 dias."
    >>> r = parse_email(txt)
    >>> r.intimacoes[0].numero_processo
    '0001234-56.2026.8.16.0001'
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

TipoAto = Literal[
    "sentenca",
    "decisao",
    "despacho",
    "publicacao",
    "edital",
    "intimacao",
    "desconhecido",
]

CNJ_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
DATE_DDMMYYYY_RE = re.compile(r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b")
DATE_YYYYMMDD_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

TIPO_ATO_PATTERNS: dict[TipoAto, re.Pattern[str]] = {
    "sentenca": re.compile(r"\bsenten[çc]a\b", re.IGNORECASE),
    "decisao": re.compile(r"\bdecis[ãa]o\b", re.IGNORECASE),
    "despacho": re.compile(r"\bdespacho\b", re.IGNORECASE),
    "edital": re.compile(r"\bedital\b", re.IGNORECASE),
    "publicacao": re.compile(r"\bpublica[çc][ãa]o\b", re.IGNORECASE),
    "intimacao": re.compile(r"\bintima[çc][ãa]o|intim[ae][\-\s]?se\b", re.IGNORECASE),
}

VARA_RE = re.compile(
    r"\b(\d+[ºa°]?\s*Vara\s+[\wÀ-ÿ\s]+?|Vara\s+\w+(?:\s+\w+){0,3})\b",
    re.IGNORECASE,
)
COMARCA_RE = re.compile(r"Comarca\s+de\s+([\wÀ-ÿ\s\-]+?)(?:\.|\n|$)", re.IGNORECASE)

PRAZO_RE = re.compile(
    r"prazo\s+(?:legal\s+)?(?:de\s+)?(\d+)\s*\(?[\wÀ-ÿ]*?\)?\s*dias?\s*(?:[úu]teis)?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Intimacao:
    """Uma intimacao extraida de email TJPR."""

    numero_processo: str
    vara: str | None = None
    comarca: str | None = None
    tipo_ato: TipoAto = "desconhecido"
    data_publicacao: date | None = None
    prazo_textual: str | None = None
    prazo_dias: int | None = None
    trecho_relevante: str = ""


@dataclass
class ParseResult:
    """Resultado do parse de um email."""

    intimacoes: list[Intimacao] = field(default_factory=list)
    total: int = 0
    erros: list[str] = field(default_factory=list)


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


def _detect_tipo_ato(text: str) -> TipoAto:
    for tipo, pattern in TIPO_ATO_PATTERNS.items():
        if pattern.search(text):
            return tipo
    return "desconhecido"


def _extract_vara(text: str) -> str | None:
    m = VARA_RE.search(text)
    if m:
        return m.group(0).strip()
    return None


def _extract_comarca(text: str) -> str | None:
    m = COMARCA_RE.search(text)
    if m:
        return m.group(1).strip()
    return None


def _extract_prazo(text: str) -> tuple[str | None, int | None]:
    m = PRAZO_RE.search(text)
    if m:
        textual = m.group(0)
        try:
            dias = int(m.group(1))
        except (ValueError, IndexError):
            dias = None
        return textual, dias
    return None, None


def _split_blocks_per_processo(text: str) -> list[tuple[str, str]]:
    """Quebra texto em blocos, um por numero de processo encontrado."""
    matches = list(CNJ_RE.finditer(text))
    if not matches:
        return []
    if len(matches) == 1:
        return [(matches[0].group(), text)]

    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(), text[start:end]))
    return blocks


def parse_email(text: str) -> ParseResult:
    """Parse email text -> ParseResult com lista de intimacoes."""
    result = ParseResult()

    if not text or not text.strip():
        result.erros.append("Texto vazio")
        return result

    data_email = _parse_date_first(text)
    blocks = _split_blocks_per_processo(text)
    if not blocks:
        result.erros.append("Nenhum numero de processo CNJ encontrado")
        return result

    for numero, bloco in blocks:
        vara = _extract_vara(bloco)
        comarca = _extract_comarca(bloco)
        tipo = _detect_tipo_ato(bloco)
        data_bloco = _parse_date_first(bloco) or data_email
        prazo_textual, prazo_dias = _extract_prazo(bloco)

        idx = bloco.find(numero)
        start_idx = max(0, idx)
        trecho = bloco[start_idx : start_idx + 200].strip()

        result.intimacoes.append(
            Intimacao(
                numero_processo=numero,
                vara=vara,
                comarca=comarca,
                tipo_ato=tipo,
                data_publicacao=data_bloco,
                prazo_textual=prazo_textual,
                prazo_dias=prazo_dias,
                trecho_relevante=trecho,
            )
        )

    result.total = len(result.intimacoes)
    return result
