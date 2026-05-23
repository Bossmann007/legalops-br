"""OAB sigilo profissional + LGPD Art. 37 — immutable audit log.

SHA-256 hash-chained audit log backed by SQLite. Each entry hashes the previous
entry's hash plus its own serialized content, enabling tamper detection via
`verify_chain()`.

LGPD: raw CPF/CNPJ/RG patterns in metadata are rejected to prevent PII leakage
into audit storage. Callers must redact identifiers (use placeholders) before
logging.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = ["AuditEntry", "AuditLog", "PIIInAuditError"]

ZERO_HASH = "0" * 64

# LGPD: regex patterns that indicate raw PII in metadata payload.
_CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_CNPJ_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
_RG_RE = re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dXx]\b")

_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("CPF", _CPF_RE),
    ("CNPJ", _CNPJ_RE),
    ("RG", _RG_RE),
)


class PIIInAuditError(ValueError):
    """Raised when metadata contains raw PII (CPF/CNPJ/RG) — must be redacted first."""


@dataclass(frozen=True)
class AuditEntry:
    """One immutable audit-log entry. ``entry_hash`` chains to the previous entry."""

    seq: int
    timestamp: datetime
    actor: str
    action: str
    resource: str
    metadata: dict[str, Any]
    prev_hash: str
    entry_hash: str


def _scan_for_pii(value: Any) -> None:
    """Recursively walk a JSON-serializable value, raising PIIInAuditError on match."""
    if isinstance(value, str):
        for name, pattern in _PII_PATTERNS:
            if pattern.search(value):
                raise PIIInAuditError(
                    f"Raw {name} pattern detected in audit metadata. "
                    "Redact PII before logging (LGPD Art. 11)."
                )
    elif isinstance(value, dict):
        for k, v in value.items():
            if isinstance(k, str):
                _scan_for_pii(k)
            _scan_for_pii(v)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _scan_for_pii(item)


def _serialize(
    seq: int,
    timestamp: datetime,
    actor: str,
    action: str,
    resource: str,
    metadata: dict[str, Any],
) -> str:
    """Deterministic JSON serialization (sorted keys) for hashing."""
    payload = {
        "seq": seq,
        "timestamp": timestamp.isoformat(),
        "actor": actor,
        "action": action,
        "resource": resource,
        "metadata": metadata,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _compute_hash(prev_hash: str, serialized: str) -> str:
    h = hashlib.sha256()
    h.update(prev_hash.encode("utf-8"))
    h.update(serialized.encode("utf-8"))
    return h.hexdigest()


def _parse_timestamp(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class AuditLog:
    """Append-only audit log with SHA-256 chain integrity."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL
                )
                """
            )

    def append(
        self,
        actor: str,
        action: str,
        resource: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Append a new entry. Atomic transaction; rejects raw PII in metadata."""
        meta = metadata if metadata is not None else {}
        _scan_for_pii(actor)
        _scan_for_pii(action)
        _scan_for_pii(resource)
        _scan_for_pii(meta)

        # Round-trip through JSON to ensure determinism + serializability up-front.
        try:
            meta_json = json.dumps(meta, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"metadata must be JSON-serializable: {exc}") from exc
        meta_normalized: dict[str, Any] = json.loads(meta_json)

        timestamp = datetime.now(UTC)

        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                "SELECT entry_hash FROM audit_log ORDER BY seq DESC LIMIT 1"
            )
            row = cur.fetchone()
            prev_hash = row["entry_hash"] if row is not None else ZERO_HASH

            cur = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM audit_log"
            )
            next_seq = int(cur.fetchone()["next_seq"])

            serialized = _serialize(
                next_seq, timestamp, actor, action, resource, meta_normalized
            )
            entry_hash = _compute_hash(prev_hash, serialized)

            conn.execute(
                """
                INSERT INTO audit_log
                    (seq, timestamp, actor, action, resource, metadata, prev_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_seq,
                    timestamp.isoformat(),
                    actor,
                    action,
                    resource,
                    meta_json,
                    prev_hash,
                    entry_hash,
                ),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

        return AuditEntry(
            seq=next_seq,
            timestamp=timestamp,
            actor=actor,
            action=action,
            resource=resource,
            metadata=meta_normalized,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )

    def _row_to_entry(self, row: sqlite3.Row) -> AuditEntry:
        return AuditEntry(
            seq=int(row["seq"]),
            timestamp=_parse_timestamp(row["timestamp"]),
            actor=row["actor"],
            action=row["action"],
            resource=row["resource"],
            metadata=json.loads(row["metadata"]),
            prev_hash=row["prev_hash"],
            entry_hash=row["entry_hash"],
        )

    def get(self, seq: int) -> AuditEntry | None:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM audit_log WHERE seq = ?", (seq,))
            row = cur.fetchone()
        return self._row_to_entry(row) if row is not None else None

    def all(self) -> list[AuditEntry]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM audit_log ORDER BY seq ASC")
            rows = cur.fetchall()
        return [self._row_to_entry(r) for r in rows]

    def latest(self) -> AuditEntry | None:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM audit_log ORDER BY seq DESC LIMIT 1")
            row = cur.fetchone()
        return self._row_to_entry(row) if row is not None else None

    def verify_chain(self) -> bool:
        """Recompute every entry's hash and confirm the chain links match storage."""
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM audit_log ORDER BY seq ASC")
            rows = cur.fetchall()

        expected_prev = ZERO_HASH
        for row in rows:
            stored_prev = row["prev_hash"]
            stored_hash = row["entry_hash"]
            if stored_prev != expected_prev:
                return False

            try:
                metadata = json.loads(row["metadata"])
                timestamp = _parse_timestamp(row["timestamp"])
            except (ValueError, json.JSONDecodeError):
                return False

            serialized = _serialize(
                int(row["seq"]),
                timestamp,
                row["actor"],
                row["action"],
                row["resource"],
                metadata,
            )
            recomputed = _compute_hash(stored_prev, serialized)
            if recomputed != stored_hash:
                return False
            expected_prev = stored_hash

        return True
