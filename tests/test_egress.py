"""Egress tests — garantem que nenhum PII bruto escape do redactor.

Le todo o corpus sintetico em corpus/synthetic/docs/, redige cada documento,
e verifica que nenhum dos identificadores originais aparece no texto redacted.

Falha = vazamento = bloqueia merge.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from legalops.pii_redactor import PIIRedactor

CORPUS_DIR = Path(__file__).parent.parent / "corpus" / "synthetic" / "docs"


def _load_corpus() -> list[dict[str, object]]:
    if not CORPUS_DIR.exists():
        pytest.skip(f"Corpus nao gerado em {CORPUS_DIR}. Rode: python corpus/synthetic/generate.py")
    docs = []
    for path in sorted(CORPUS_DIR.glob("doc_*.json")):
        docs.append(json.loads(path.read_text(encoding="utf-8")))
    return docs


@pytest.fixture(scope="module")
def corpus() -> list[dict[str, object]]:
    return _load_corpus()


@pytest.fixture(scope="module")
def redactor() -> PIIRedactor:
    return PIIRedactor(salt="test-salt-egress-v1")


LEAK_PATTERNS = {
    "CPF": re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}"),
    "CNPJ": re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"),
    "OAB": re.compile(r"OAB[/-][A-Z]{2}\s?\d+"),
    "EMAIL": re.compile(r"[\w.+-]+@[\w.-]+\.\w+"),
    "PIX_UUID": re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
}


class TestEgress:
    def test_no_raw_pii_in_redacted(
        self, corpus: list[dict[str, object]], redactor: PIIRedactor
    ) -> None:
        leaks: list[tuple[str, str, str]] = []
        for doc in corpus:
            text = doc["text"]
            assert isinstance(text, str)
            result = redactor.redact(text)
            for label, pat in LEAK_PATTERNS.items():
                for m in pat.finditer(result.redacted_text):
                    if m.group().startswith("["):
                        continue
                    leaks.append((str(doc["id"]), label, m.group()))
        assert not leaks, f"Vazamento detectado: {leaks[:5]}"

    def test_match_count_meets_expected(
        self, corpus: list[dict[str, object]], redactor: PIIRedactor
    ) -> None:
        ok = 0
        for doc in corpus:
            text = doc["text"]
            expected = int(doc["expected_pii_count"])  # type: ignore[arg-type]
            assert isinstance(text, str)
            result = redactor.redact(text)
            if len(result.matches) >= expected:
                ok += 1
        ratio = ok / len(corpus) if corpus else 0
        assert ratio >= 0.80, f"Apenas {ratio:.1%} dos docs tem match count esperado"

    def test_corpus_is_synthetic_marker(self, corpus: list[dict[str, object]]) -> None:
        for doc in corpus:
            assert str(doc["id"]).startswith("synthetic-"), (
                "Corpus nao sintetico detectado — abortar"
            )
