"""PII Redactor BR — detecta e mascara identificadores brasileiros antes de enviar a LLMs.

Patterns: CPF, CNPJ, RG, OAB, PIX (email/phone/uuid), email, telefone BR.

Uso:
    >>> from legalops.pii_redactor import PIIRedactor
    >>> r = PIIRedactor()
    >>> result = r.redact("Cliente CPF 123.456.789-00 ajuizou ação")
    >>> "123.456.789-00" not in result.redacted_text
    True
    >>> len(result.matches)
    1
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Literal

PIIType = Literal[
    "CPF",
    "CNPJ",
    "RG",
    "OAB",
    "PIX_UUID",
    "EMAIL",
    "PHONE_BR",
]


@dataclass(frozen=True)
class Match:
    """Single PII match in redacted text."""

    pii_type: PIIType
    placeholder: str
    span: tuple[int, int]
    sha256: str


@dataclass
class RedactionResult:
    """Output of `PIIRedactor.redact()`."""

    redacted_text: str
    matches: list[Match] = field(default_factory=list)

    @property
    def has_pii(self) -> bool:
        return len(self.matches) > 0


# Patterns ordered by specificity (longer/more-specific first)
PATTERNS: dict[PIIType, re.Pattern[str]] = {
    "CNPJ": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "RG": re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dXx]\b"),
    "OAB": re.compile(r"\bOAB[/-]?[A-Z]{2}\s?\d{1,6}\b"),
    "PIX_UUID": re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    ),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "PHONE_BR": re.compile(r"\+?55?\s?\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b"),
}


class PIIRedactor:
    """Redact Brazilian PII from text before sending to LLMs.

    Strategy:
    - Run patterns in order of specificity (CNPJ → CPF → RG → OAB → PIX UUID → email → phone)
    - Replace each match with `[TYPE_<sha256_6>]` placeholder
    - Store deterministic salted SHA-256 of original for audit reconciliation
    - Track spans in ORIGINAL text for downstream alignment
    """

    def __init__(self, salt: str = "legalops-br-v0.1") -> None:
        self._salt = salt.encode("utf-8")

    def _hash_full(self, value: str) -> str:
        return hashlib.sha256(self._salt + value.encode("utf-8")).hexdigest()

    def _placeholder(self, pii_type: PIIType, original: str) -> str:
        return f"[{pii_type}_{self._hash_full(original)[:6]}]"

    def redact(self, text: str) -> RedactionResult:
        """Redact PII in `text`. Returns redacted copy + match metadata.

        Args:
            text: Plain text input. Never logged.

        Returns:
            RedactionResult with redacted_text and matches list (ordered by span ascending).
        """
        matches: list[Match] = []
        seen_spans: set[tuple[int, int]] = set()

        all_hits: list[tuple[int, int, PIIType, str]] = []
        for pii_type, pattern in PATTERNS.items():
            for m in pattern.finditer(text):
                start, end = m.span()
                if any(s <= start < e or s < end <= e for s, e in seen_spans):
                    continue
                seen_spans.add((start, end))
                all_hits.append((start, end, pii_type, m.group()))

        # Replace from end to start to preserve earlier indices
        all_hits.sort(key=lambda x: x[0], reverse=True)
        redacted = text
        for start, end, pii_type, original in all_hits:
            placeholder = self._placeholder(pii_type, original)
            sha = self._hash_full(original)
            matches.append(
                Match(
                    pii_type=pii_type,
                    placeholder=placeholder,
                    span=(start, end),
                    sha256=sha,
                )
            )
            redacted = redacted[:start] + placeholder + redacted[end:]

        matches.reverse()
        return RedactionResult(redacted_text=redacted, matches=matches)
