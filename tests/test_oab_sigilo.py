"""Tests for legalops.oab_sigilo — hash-chain integrity + LGPD PII guard."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from legalops.oab_sigilo import AUDIT_HMAC_ENV, ZERO_HASH, AuditEntry, AuditLog, PIIInAuditError


@pytest.fixture
def audit_db(tmp_path: Path) -> Path:
    return tmp_path / "audit.db"


@pytest.fixture
def log(audit_db: Path) -> AuditLog:
    return AuditLog(audit_db)


def test_first_append_uses_zero_prev_hash(log: AuditLog) -> None:
    entry = log.append(
        actor="agent:tjpr_parser",
        action="redact",
        resource="process:PLACEHOLDER-001",
        metadata={"reason": "smoke"},
    )
    assert entry.seq == 1
    assert entry.prev_hash == ZERO_HASH
    assert len(entry.entry_hash) == 64
    assert entry.entry_hash != ZERO_HASH


def test_second_append_chains_to_first(log: AuditLog) -> None:
    first = log.append("agent:a", "calc_prazo", "process:PH-1", {"step": 1})
    second = log.append("agent:b", "send_message", "msg:PH-2", {"step": 2})
    assert second.seq == 2
    assert second.prev_hash == first.entry_hash
    assert second.entry_hash != first.entry_hash


def test_verify_chain_valid(log: AuditLog) -> None:
    log.append("agent:a", "redact", "res:1", {"k": "v"})
    log.append("agent:b", "redact", "res:2", {"k": 2})
    log.append("agent:c", "redact", "res:3", {"nested": {"x": [1, 2, 3]}})
    assert log.verify_chain() is True


def test_verify_chain_detects_tamper_on_metadata(audit_db: Path) -> None:
    log = AuditLog(audit_db)
    log.append("agent:a", "redact", "res:1", {"k": "v"})
    log.append("agent:b", "redact", "res:2", {"k": "v2"})
    assert log.verify_chain() is True

    # Tamper: mutate row 1's metadata directly in SQLite
    with sqlite3.connect(audit_db) as conn:
        conn.execute(
            "UPDATE audit_log SET metadata = ? WHERE seq = ?",
            ('{"k":"tampered"}', 1),
        )
        conn.commit()

    assert log.verify_chain() is False


def test_verify_chain_detects_tamper_on_actor(audit_db: Path) -> None:
    log = AuditLog(audit_db)
    log.append("agent:a", "redact", "res:1", {})
    log.append("agent:b", "redact", "res:2", {})

    with sqlite3.connect(audit_db) as conn:
        conn.execute("UPDATE audit_log SET actor = ? WHERE seq = ?", ("agent:hacker", 1))
        conn.commit()

    assert log.verify_chain() is False


def test_pii_cpf_rejected(log: AuditLog) -> None:
    with pytest.raises(PIIInAuditError):
        log.append(
            actor="agent:x",
            action="redact",
            resource="process:PH",
            metadata={"note": "paciente CPF 123.456.789-00 cadastrado"},
        )


def test_pii_cpf_rejected_nested(log: AuditLog) -> None:
    with pytest.raises(PIIInAuditError):
        log.append(
            "agent:x",
            "redact",
            "process:PH",
            {"audit": {"items": ["ok", "123.456.789-00"]}},
        )


def test_pii_cnpj_rejected(log: AuditLog) -> None:
    with pytest.raises(PIIInAuditError):
        log.append(
            "agent:x",
            "redact",
            "process:PH",
            {"empresa": "12.345.678/0001-90"},
        )


def test_pii_rejected_does_not_persist(log: AuditLog) -> None:
    with pytest.raises(PIIInAuditError):
        log.append("agent:x", "redact", "res:1", {"cpf": "123.456.789-00"})
    assert log.all() == []
    assert log.latest() is None


def test_get_missing_returns_none(log: AuditLog) -> None:
    assert log.get(99999) is None


def test_get_returns_entry(log: AuditLog) -> None:
    appended = log.append("agent:a", "redact", "res:1", {"k": "v"})
    fetched = log.get(1)
    assert fetched is not None
    assert fetched.seq == 1
    assert fetched.actor == "agent:a"
    assert fetched.entry_hash == appended.entry_hash


def test_latest_returns_last_entry(log: AuditLog) -> None:
    assert log.latest() is None
    log.append("agent:a", "redact", "res:1", {})
    log.append("agent:b", "redact", "res:2", {})
    third = log.append("agent:c", "redact", "res:3", {})
    latest = log.latest()
    assert latest is not None
    assert latest.seq == 3
    assert latest.actor == "agent:c"
    assert latest.entry_hash == third.entry_hash


def test_all_returns_entries_ordered_by_seq(log: AuditLog) -> None:
    log.append("agent:a", "redact", "res:1", {})
    log.append("agent:b", "redact", "res:2", {})
    log.append("agent:c", "redact", "res:3", {})
    entries = log.all()
    assert [e.seq for e in entries] == [1, 2, 3]
    assert [e.actor for e in entries] == ["agent:a", "agent:b", "agent:c"]
    assert all(isinstance(e, AuditEntry) for e in entries)


def test_all_empty(log: AuditLog) -> None:
    assert log.all() == []


def test_metadata_default_is_empty_dict(log: AuditLog) -> None:
    entry = log.append("agent:a", "redact", "res:1")
    assert entry.metadata == {}
    fetched = log.get(1)
    assert fetched is not None
    assert fetched.metadata == {}


class TestHMACTamperEvidence:
    """M1: tamper-evidence via HMAC-SHA256 com chave secreta."""

    _KEY = "test-hmac-key-32-bytes-synthetic!!"  # noqa: S105 — test fixture

    def test_hmac_chain_verifies_with_same_key(self, audit_db: Path) -> None:
        log = AuditLog(audit_db, hmac_key=self._KEY)
        log.append("agent:a", "redact", "res:1", {"k": "v"})
        log.append("agent:b", "redact", "res:2", {"k": "v2"})
        assert log.verify_chain() is True

    def test_hmac_detects_metadata_tamper(self, audit_db: Path) -> None:
        log = AuditLog(audit_db, hmac_key=self._KEY)
        log.append("agent:a", "redact", "res:1", {"k": "v"})
        log.append("agent:b", "redact", "res:2", {"k": "v2"})
        with sqlite3.connect(audit_db) as conn:
            conn.execute(
                "UPDATE audit_log SET metadata = ? WHERE seq = ?",
                ('{"k":"tampered"}', 1),
            )
            conn.commit()
        assert log.verify_chain() is False

    def test_chain_built_with_key_fails_without_key(self, audit_db: Path) -> None:
        # Atacante que rouba o DB mas nao tem a chave nao consegue verificar.
        log_with_key = AuditLog(audit_db, hmac_key=self._KEY)
        log_with_key.append("agent:a", "redact", "res:1", {"k": "v"})
        log_with_key.append("agent:b", "redact", "res:2", {"k": "v2"})

        log_without_key = AuditLog(audit_db)
        assert log_without_key.verify_chain() is False

    def test_chain_built_without_key_fails_with_key(self, audit_db: Path) -> None:
        # Simetrico: chain plain-SHA256 nao verifica como HMAC.
        log_plain = AuditLog(audit_db)
        log_plain.append("agent:a", "redact", "res:1", {"k": "v"})

        log_hmac = AuditLog(audit_db, hmac_key=self._KEY)
        assert log_hmac.verify_chain() is False

    def test_different_keys_fail_cross_verification(self, audit_db: Path) -> None:
        log_a = AuditLog(audit_db, hmac_key="key-alpha-32-bytes-synthetic-pad!")
        log_a.append("agent:a", "redact", "res:1", {})
        log_a.append("agent:b", "redact", "res:2", {})

        log_b = AuditLog(audit_db, hmac_key="key-bravo-32-bytes-synthetic-pad!")
        assert log_b.verify_chain() is False

    def test_env_var_provides_key(self, audit_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUDIT_HMAC_ENV, self._KEY)
        log = AuditLog(audit_db)
        log.append("agent:a", "redact", "res:1", {"k": "v"})
        assert log.verify_chain() is True

        # Sem env nem param: cai pra SHA-256 puro → nao verifica chain do HMAC.
        monkeypatch.delenv(AUDIT_HMAC_ENV)
        log_plain = AuditLog(audit_db)
        assert log_plain.verify_chain() is False

    def test_explicit_key_overrides_env(
        self, audit_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(AUDIT_HMAC_ENV, "env-key-should-be-overridden-pad!")
        log = AuditLog(audit_db, hmac_key=self._KEY)
        log.append("agent:a", "redact", "res:1", {})
        assert log.verify_chain() is True

    def test_bytes_key_accepted(self, audit_db: Path) -> None:
        log = AuditLog(audit_db, hmac_key=self._KEY.encode("utf-8"))
        log.append("agent:a", "redact", "res:1", {})
        assert log.verify_chain() is True


def test_persistence_across_instances(audit_db: Path) -> None:
    log1 = AuditLog(audit_db)
    log1.append("agent:a", "redact", "res:1", {"k": "v"})
    log1.append("agent:b", "redact", "res:2", {"k": "v2"})

    log2 = AuditLog(audit_db)
    assert len(log2.all()) == 2
    assert log2.verify_chain() is True
    latest = log2.latest()
    assert latest is not None
    assert latest.seq == 2

    third = log2.append("agent:c", "redact", "res:3", {})
    assert third.seq == 3
    assert log2.verify_chain() is True
