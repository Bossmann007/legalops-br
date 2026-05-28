"""Detecta tribunal a partir de email (sender domain + header fingerprint).

Roda ANTES dos parsers especificos no orchestrator para rotear corretamente.

Uso:
    >>> from legalops.tribunal_detector import detect_tribunal
    >>> detect_tribunal("Sistema e-SAJ\\nFOO", sender="x@tjsp.jus.br")
    'tjsp'
"""

from __future__ import annotations

import re
from typing import Literal

Tribunal = Literal["tjsp", "tjpr", "tjsc", "tjrj", "unknown"]

_TJSP_DOMAIN_RE = re.compile(r"@(?:[\w.-]+\.)?tjsp\.jus\.br\b", re.IGNORECASE)
_TJPR_DOMAIN_RE = re.compile(r"@(?:[\w.-]+\.)?tjpr\.jus\.br\b", re.IGNORECASE)
_TJSC_DOMAIN_RE = re.compile(r"@(?:[\w.-]+\.)?tjsc\.jus\.br\b", re.IGNORECASE)
_TJRJ_DOMAIN_RE = re.compile(r"@(?:[\w.-]+\.)?tjrj\.jus\.br\b", re.IGNORECASE)

_TJSP_HEADER_RE = re.compile(
    r"\b(e[-\s]?SAJ|PJe[-\s]?SP|Tribunal de Justi[çc]a de S[ãa]o Paulo)\b",
    re.IGNORECASE,
)
_TJPR_HEADER_RE = re.compile(
    r"\b(Projudi|Tribunal de Justi[çc]a do Paran[áa])\b",
    re.IGNORECASE,
)
_TJSC_HEADER_RE = re.compile(
    r"\b(e[-\s]?Proc|Tribunal de Justi[çc]a de Santa Catarina)\b",
    re.IGNORECASE,
)
_TJRJ_HEADER_RE = re.compile(
    r"\b(PJe[-\s]?RJ|Tribunal de Justi[çc]a do (?:Estado do )?Rio de Janeiro)\b",
    re.IGNORECASE,
)


def detect_tribunal(email_text: str, sender: str = "") -> Tribunal:
    """Identifica tribunal via sender domain (prioridade) ou header fingerprint.

    Args:
        email_text: corpo do email (apos redact OK).
        sender: campo From: do email (opcional). Domain match precede header.

    Returns:
        "tjsp" | "tjpr" | "unknown"
    """
    if sender:
        if _TJSP_DOMAIN_RE.search(sender):
            return "tjsp"
        if _TJPR_DOMAIN_RE.search(sender):
            return "tjpr"
        if _TJSC_DOMAIN_RE.search(sender):
            return "tjsc"
        if _TJRJ_DOMAIN_RE.search(sender):
            return "tjrj"

    if _TJSP_HEADER_RE.search(email_text):
        return "tjsp"
    if _TJPR_HEADER_RE.search(email_text):
        return "tjpr"
    if _TJSC_HEADER_RE.search(email_text):
        return "tjsc"
    if _TJRJ_HEADER_RE.search(email_text):
        return "tjrj"

    return "unknown"
