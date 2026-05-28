"""Parser de emails do TJRJ (PJe-RJ + sistema TJRJ legado).

Implementacao standalone com regex especificas do PJe-RJ:
- Header: "PJe-RJ" / "PJe Rio de Janeiro" / "Tribunal de Justica do Estado do Rio de Janeiro"
- Label processo: "Processo n." / "Processo numero:" / "Autos:"
- CNJ tribunal 8.19
- Vara ordinal + Civel/Criminal/Empresarial/Fazenda + Capital|Comarca de X
- "Cartorio" comum em emails antigos
- Prazos: "prazo de N dias", "em N dias", "no prazo legal de N dias"
"""

from __future__ import annotations

import re
from datetime import date

from legalops.tjpr_parser import Intimacao, ParseResult, TipoAto

__all__ = ["Intimacao", "ParseResult", "TipoAto", "parse_email"]

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

# PJe-RJ: "Na. Vara Civel/Criminal/Empresarial/Fazenda Publica" + capital/comarca
VARA_RE = re.compile(
    r"\b(\d+[ºªa°]?\s*Vara\s+"
    r"(?:C[íi]vel|Criminal|Empresarial|Fazenda(?:\s+P[úu]blica)?|"
    r"Fam[íi]lia|Trabalhista|Federal|[\wÀ-ÿ]+)"
    r"(?:\s+[\wÀ-ÿ]+){0,4})\b",
    re.IGNORECASE,
)
# "Comarca de X" ou "Comarca da Capital" ou apenas "Capital"
COMARCA_RE = re.compile(
    r"Comarca\s+(?:de\s+|da\s+)([\wÀ-ÿ\s\-]+?)(?:[\.\n,]|$)",
    re.IGNORECASE,
)
CARTORIO_RE = re.compile(
    r"\b(\d+[ºªao°]?\s*Cart[óo]rio\s+[\wÀ-ÿ\s]+?)(?:[\.\n,]|$)",
    re.IGNORECASE,
)

# Cobre: "prazo de N dias", "em N dias", "no prazo legal de N dias"
PRAZO_RE = re.compile(
    r"(?:no\s+)?prazo\s+(?:legal\s+)?(?:de\s+)?(\d+)\s*\(?[\wÀ-ÿ]*?\)?\s*dias?\s*(?:[úu]teis)?",
    re.IGNORECASE,
)
PRAZO_EM_RE = re.compile(
    r"\bem\s+(\d+)\s*\(?[\wÀ-ÿ]*?\)?\s*dias?\s*(?:[úu]teis)?",
    re.IGNORECASE,
)


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
    # Fallback: cartorio em emails legados
    c = CARTORIO_RE.search(text)
    if c:
        return c.group(1).strip()
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
    m2 = PRAZO_EM_RE.search(text)
    if m2:
        textual = m2.group(0)
        try:
            dias = int(m2.group(1))
        except (ValueError, IndexError):
            dias = None
        return textual, dias
    return None, None


def _split_blocks_per_processo(text: str) -> list[tuple[str, str]]:
    """Quebra texto em blocos, um por numero CNJ encontrado."""
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
    """Parse texto de email TJRJ (PJe-RJ) -> ParseResult."""
    result = ParseResult()

    if not text or not text.strip():
        result.erros.append("Texto vazio")
        return result

    data_email = _parse_date_first(text)
    blocks = _split_blocks_per_processo(text)
    if not blocks:
        result.erros.append("Nenhum numero CNJ encontrado")
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
