"""Gate de aprovacao para escrita em ficha/financeiro (write/rollback).

Garante a regra "nenhuma escrita em ficha ou financeiro sem aprovacao
explicita". Cada mudanca passa por solicitacao -> aprovacao/rejeicao ->
commit, e cada transicao e registrada no ``AuditLog`` imutavel (LGPD Art. 37).

LGPD: o payload da mudanca nunca e enviado ao audit log — apenas metadados sem
PII (change_id, resource, status). O AuditLog ja rejeita PII bruto; nao
duplicamos essa logica aqui.

Uso:
    >>> from pathlib import Path
    >>> from legalops.oab_sigilo import AuditLog
    >>> from legalops.approval_gate import ApprovalGate
    >>> gate = ApprovalGate(AuditLog(Path("/tmp/a.db")))
    >>> pc = gate.request("agent:x", "ficha:PLACEHOLDER", "update", {"k": 1})
    >>> pc.status
    'pending'
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from legalops.oab_sigilo import AuditLog

__all__ = ["ApprovalError", "ApprovalGate", "PendingChange"]

ChangeStatus = Literal["pending", "approved", "rejected"]


class ApprovalError(RuntimeError):
    """Levantado quando se tenta commitar uma mudanca nao aprovada."""


@dataclass(frozen=True)
class PendingChange:
    """Uma mudanca pendente em recurso protegido (ficha/financeiro)."""

    change_id: str
    actor: str
    resource: str
    description: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: ChangeStatus = "pending"


class ApprovalGate:
    """Gate em memoria que exige aprovacao antes de aplicar mudancas.

    Mantem as mudancas pendentes num dicionario em memoria e registra cada
    transicao no ``AuditLog`` fornecido.
    """

    def __init__(self, audit_log: AuditLog) -> None:
        self._audit = audit_log
        self._changes: dict[str, PendingChange] = {}

    def _get_or_raise(self, change_id: str) -> PendingChange:
        change = self._changes.get(change_id)
        if change is None:
            raise ApprovalError(f"Mudanca desconhecida: {change_id}")
        return change

    def request(
        self,
        actor: str,
        resource: str,
        description: str,
        payload: dict[str, Any],
    ) -> PendingChange:
        """Solicita uma mudanca; entra como ``pending`` e registra no audit.

        Args:
            actor: Quem solicita a mudanca.
            resource: Recurso alvo (ex.: ``ficha:PLACEHOLDER-001``).
            description: Descricao curta e sem PII da mudanca.
            payload: Dados a aplicar no commit (nao vao para o audit).

        Returns:
            A ``PendingChange`` criada com status ``pending``.
        """
        change_id = uuid.uuid4().hex
        change = PendingChange(
            change_id=change_id,
            actor=actor,
            resource=resource,
            description=description,
            payload=dict(payload),
            status="pending",
        )
        self._changes[change_id] = change
        self._audit.append(
            actor=actor,
            action="change_requested",
            resource=resource,
            metadata={"change_id": change_id, "status": "pending"},
        )
        return change

    def approve(self, change_id: str, approver: str) -> PendingChange:
        """Aprova uma mudanca pendente e registra no audit.

        Args:
            change_id: Identificador da mudanca.
            approver: Quem aprova.

        Returns:
            A ``PendingChange`` com status ``approved``.

        Raises:
            ApprovalError: Se a mudanca nao existir.
        """
        change = self._get_or_raise(change_id)
        updated = PendingChange(
            change_id=change.change_id,
            actor=change.actor,
            resource=change.resource,
            description=change.description,
            payload=change.payload,
            status="approved",
        )
        self._changes[change_id] = updated
        self._audit.append(
            actor=approver,
            action="change_approved",
            resource=change.resource,
            metadata={"change_id": change_id, "status": "approved"},
        )
        return updated

    def reject(self, change_id: str, approver: str, reason: str) -> PendingChange:
        """Rejeita uma mudanca pendente e registra no audit.

        Args:
            change_id: Identificador da mudanca.
            approver: Quem rejeita.
            reason: Motivo (sem PII) da rejeicao.

        Returns:
            A ``PendingChange`` com status ``rejected``.

        Raises:
            ApprovalError: Se a mudanca nao existir.
        """
        change = self._get_or_raise(change_id)
        updated = PendingChange(
            change_id=change.change_id,
            actor=change.actor,
            resource=change.resource,
            description=change.description,
            payload=change.payload,
            status="rejected",
        )
        self._changes[change_id] = updated
        self._audit.append(
            actor=approver,
            action="change_rejected",
            resource=change.resource,
            metadata={"change_id": change_id, "status": "rejected", "reason": reason},
        )
        return updated

    def commit(self, change_id: str, apply_fn: Callable[[dict[str, Any]], None]) -> None:
        """Aplica uma mudanca aprovada chamando ``apply_fn(payload)``.

        Args:
            change_id: Identificador da mudanca.
            apply_fn: Funcao que efetiva a escrita recebendo o payload.

        Raises:
            ApprovalError: Se a mudanca nao existir ou nao estiver aprovada.
        """
        change = self._get_or_raise(change_id)
        if change.status != "approved":
            raise ApprovalError(
                f"Mudanca {change_id} nao aprovada (status={change.status}); commit bloqueado."
            )
        apply_fn(dict(change.payload))
        self._audit.append(
            actor=change.actor,
            action="change_committed",
            resource=change.resource,
            metadata={"change_id": change_id, "status": "approved"},
        )

    def pending(self) -> list[PendingChange]:
        """Retorna a lista de mudancas com status ``pending``."""
        return [c for c in self._changes.values() if c.status == "pending"]
