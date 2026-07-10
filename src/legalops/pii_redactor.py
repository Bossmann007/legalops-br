"""PII Redactor BR — detecta e mascara identificadores brasileiros antes de enviar a LLMs.

Patterns: CPF, CNPJ, RG, OAB, PIX (email/phone/uuid), email, telefone BR.

Uso:
    >>> from legalops.pii_redactor import PIIRedactor
    >>> r = PIIRedactor(salt="exemplo-salt-secreto-32bytes!!")
    >>> result = r.redact("Cliente CPF 123.456.789-00 ajuizou ação")
    >>> "123.456.789-00" not in result.redacted_text
    True
    >>> len(result.matches)
    1
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from legalops.br_validators import is_valid_cnpj, is_valid_cpf

#: Variavel de ambiente que fornece o salt secreto da pseudonimizacao.
SALT_ENV_VAR = "LEGALOPS_PII_SALT"


class MissingSaltError(RuntimeError):
    """Salt secreto ausente.

    Sem salt secreto o hash do audit vira reversivel por forca bruta (espaco CPF
    pequeno), o que derrota a pseudonimizacao (Art. 13 LGPD). Defina
    ``LEGALOPS_PII_SALT`` com segredo aleatorio (>=16 bytes) ou passe ``salt=``.
    """


PIIType = Literal[
    "CPF",
    "CNPJ",
    "RG",
    "OAB",
    "PIX_UUID",
    "EMAIL",
    "PHONE_BR",
    "CPF_NUMERIC",
    "CNPJ_NUMERIC",
    "NOME",
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


# Patterns ordered by specificity (longer/more-specific first).
# Numeric variants (sem mascara) ficam por ultimo + tem validator gate.
PATTERNS: dict[PIIType, re.Pattern[str]] = {
    "CNPJ": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "RG": re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dXx]\b"),
    "OAB": re.compile(r"\bOAB[/-]?[A-Z]{2}\s?\d{1,6}\b"),
    "PIX_UUID": re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    ),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # Exige separador "-" no numero local: desambigua de CPF/CNPJ em digitos puros.
    "PHONE_BR": re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}-\d{4}\b"),
    # CNJ format NNNNNNN-DD.AAAA.J.TR.OOOO ~ 25 digitos; PIX UUID = 32 hex
    # 14 digitos puros = CNPJ; 11 = CPF. Validator dv reduz falso positivo.
    "CNPJ_NUMERIC": re.compile(r"\b\d{14}\b"),
    "CPF_NUMERIC": re.compile(r"\b\d{11}\b"),
}

# Validators opcionais por tipo. So redige se validator (se presente) retornar True.
PATTERN_VALIDATORS: dict[PIIType, Callable[[str], bool]] = {
    "CPF_NUMERIC": is_valid_cpf,
    "CNPJ_NUMERIC": is_valid_cnpj,
}

_NAME_PREFIX_RE = re.compile(
    r"\b(?:AUTOR|R[ÉE]U|RECLAMANTE|RECLAMADO|REQUERENTE|REQUERIDO|"
    r"EXEQUENTE|EXECUTADO|INTIMADO|ADVOGAD[OA]|PATRONO)\b:?"
    r"|\b(?:Dr|Dra|Sr|Sra)\.\s*",
    re.IGNORECASE,
)
_CAPITALIZED_WORD_RE = re.compile(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÖØ-öø-ÿ']*")
_NAME_CONNECTORS = {"de", "da", "do", "das", "dos", "e"}
_ALIAS_RE = re.compile(r"CLI-\d+\b", re.IGNORECASE)


def _name_span_after_prefix(
    text: str, pos: int, blocked: set[tuple[int, int]]
) -> tuple[int, int] | None:
    start = pos
    while start < len(text) and text[start] in " \t":
        start += 1
    if start >= len(text) or text[start] in "\r\n,.;:()[]{}":
        return None
    if _ALIAS_RE.match(text, start):
        return None

    cur = start
    last_cap_end: int | None = None
    saw_capitalized = False
    while cur < len(text):
        while cur < len(text) and text[cur] == " ":
            cur += 1
        if cur >= len(text) or text[cur] in "\r\n,.;:()[]{}":
            break

        word_match = re.match(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text[cur:])
        if not word_match:
            break
        word = word_match.group()
        end = cur + len(word)
        # Nao deixe o nome invadir um match estrutural ja reivindicado (ex: OAB,
        # CPF logo apos o nome). Sem isto, o span do nome engole "OAB", colide, e
        # o overlap-dedup descartaria o nome inteiro — vazando-o. Trunca antes.
        if any(cur < e and s < end for s, e in blocked):
            break
        if _CAPITALIZED_WORD_RE.fullmatch(word):
            saw_capitalized = True
            last_cap_end = end
            cur = end
            continue
        if saw_capitalized and word.lower() in _NAME_CONNECTORS:
            cur = end
            continue
        break

    if last_cap_end is None:
        return None
    return start, last_cap_end


class PIIRedactor:
    """Redact Brazilian PII from text before sending to LLMs.

    Strategy:
    - Run patterns in order of specificity (CNPJ → CPF → RG → OAB → PIX UUID → email → phone)
    - Replace each match with `[TYPE_<hmac_6>]` placeholder
    - Store deterministic HMAC-SHA256 (secret salt) of original for audit reconciliation
    - Track spans in ORIGINAL text for downstream alignment
    """

    _MIN_SALT_LEN = 16

    def __init__(self, salt: str | None = None) -> None:
        """Cria o redactor.

        Args:
            salt: Salt secreto. Se ``None``, le de ``LEGALOPS_PII_SALT``.

        Raises:
            MissingSaltError: Salt ausente (env nao definido e ``salt`` None).
            ValueError: Salt mais curto que ``_MIN_SALT_LEN`` bytes.
        """
        resolved = salt if salt is not None else os.environ.get(SALT_ENV_VAR)
        if not resolved:
            raise MissingSaltError(
                f"Salt secreto obrigatorio: defina {SALT_ENV_VAR} ou passe salt=."
            )
        raw = resolved.encode("utf-8")
        if len(raw) < self._MIN_SALT_LEN:
            raise ValueError(f"Salt muito curto ({len(raw)}B); minimo {self._MIN_SALT_LEN}B.")
        self._salt = raw

    def _hash_full(self, value: str) -> str:
        return hmac.new(self._salt, value.encode("utf-8"), hashlib.sha256).hexdigest()

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
            validator = PATTERN_VALIDATORS.get(pii_type)
            for m in pattern.finditer(text):
                start, end = m.span()
                # Overlap de intervalos (cobre tambem containment em ambos sentidos).
                if any(start < e and s < end for s, e in seen_spans):
                    continue
                if validator is not None and not validator(m.group()):
                    continue
                seen_spans.add((start, end))
                all_hits.append((start, end, pii_type, m.group()))

        for prefix_match in _NAME_PREFIX_RE.finditer(text):
            span = _name_span_after_prefix(text, prefix_match.end(), seen_spans)
            if span is None:
                continue
            start, end = span
            if any(start < e and s < end for s, e in seen_spans):
                continue
            seen_spans.add((start, end))
            all_hits.append((start, end, "NOME", text[start:end]))

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
