"""Fixtures globais da suite de testes.

Define um salt de PII sintetico no ambiente para que ``PIIRedactor`` (e o
``process_email`` que o usa por padrao) funcionem sem exigir configuracao real.
NUNCA usar este salt em producao — e publico e somente para testes.
"""

from __future__ import annotations

import pytest

from legalops.pii_redactor import SALT_ENV_VAR

_TEST_SALT = "test-suite-synthetic-salt-v1"


@pytest.fixture(autouse=True)
def _pii_salt_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Garante LEGALOPS_PII_SALT definido em todo teste (salt sintetico)."""
    monkeypatch.setenv(SALT_ENV_VAR, _TEST_SALT)
