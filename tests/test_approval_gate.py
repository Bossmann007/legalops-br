"""Tests for legalops.approval_gate — lifecycle de aprovacao + audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from legalops.approval_gate import ApprovalError, ApprovalGate, PendingChange
from legalops.oab_sigilo import AuditLog


@pytest.fixture
def gate(tmp_path: Path) -> ApprovalGate:
    return ApprovalGate(AuditLog(tmp_path / "audit.db"))


def test_request_cria_pending(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update nome", {"nome": "X"})

    assert change.status == "pending"


def test_request_gera_change_id(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    assert change.change_id


def test_request_aparece_em_pending(gate: ApprovalGate) -> None:
    gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    assert len(gate.pending()) == 1


def test_request_loga_audit(gate: ApprovalGate, tmp_path: Path) -> None:
    gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    entries = AuditLog(tmp_path / "audit.db").all()
    assert entries[0].action == "change_requested"


def test_approve_muda_status(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    approved = gate.approve(change.change_id, "tia_may")

    assert approved.status == "approved"


def test_approve_sai_de_pending(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    gate.approve(change.change_id, "tia_may")

    assert gate.pending() == []


def test_approve_loga_audit(gate: ApprovalGate, tmp_path: Path) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    gate.approve(change.change_id, "tia_may")

    actions = [e.action for e in AuditLog(tmp_path / "audit.db").all()]
    assert "change_approved" in actions


def test_approve_desconhecido_lanca(gate: ApprovalGate) -> None:
    with pytest.raises(ApprovalError):
        gate.approve("inexistente", "tia_may")


def test_reject_muda_status(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    rejected = gate.reject(change.change_id, "tia_may", "fora de escopo")

    assert rejected.status == "rejected"


def test_reject_loga_audit(gate: ApprovalGate, tmp_path: Path) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    gate.reject(change.change_id, "tia_may", "fora de escopo")

    actions = [e.action for e in AuditLog(tmp_path / "audit.db").all()]
    assert "change_rejected" in actions


def test_reject_desconhecido_lanca(gate: ApprovalGate) -> None:
    with pytest.raises(ApprovalError):
        gate.reject("inexistente", "tia_may", "motivo")


def test_commit_aplica_apos_aprovacao(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "financeiro:F-001", "lancar", {"valor": 100})
    gate.approve(change.change_id, "tia_may")
    aplicado: dict[str, Any] = {}

    gate.commit(change.change_id, lambda p: aplicado.update(p))

    assert aplicado == {"valor": 100}


def test_commit_loga_audit(gate: ApprovalGate, tmp_path: Path) -> None:
    change = gate.request("agent:x", "financeiro:F-001", "lancar", {"valor": 100})
    gate.approve(change.change_id, "tia_may")

    gate.commit(change.change_id, lambda _p: None)

    actions = [e.action for e in AuditLog(tmp_path / "audit.db").all()]
    assert "change_committed" in actions


def test_commit_antes_de_aprovar_lanca(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})

    with pytest.raises(ApprovalError):
        gate.commit(change.change_id, lambda _p: None)


def test_commit_apos_reject_lanca(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})
    gate.reject(change.change_id, "tia_may", "negado")

    with pytest.raises(ApprovalError):
        gate.commit(change.change_id, lambda _p: None)


def test_commit_desconhecido_lanca(gate: ApprovalGate) -> None:
    with pytest.raises(ApprovalError):
        gate.commit("inexistente", lambda _p: None)


def test_commit_nao_chama_apply_se_nao_aprovado(gate: ApprovalGate) -> None:
    change = gate.request("agent:x", "ficha:P-001", "update", {"k": 1})
    chamado: list[bool] = []

    with pytest.raises(ApprovalError):
        gate.commit(change.change_id, lambda _p: chamado.append(True))

    assert chamado == []


def test_audit_metadata_nao_contem_payload(gate: ApprovalGate, tmp_path: Path) -> None:
    gate.request("agent:x", "ficha:P-001", "update", {"segredo": "valor"})

    meta = AuditLog(tmp_path / "audit.db").all()[0].metadata
    assert "segredo" not in meta


def test_chain_integro_apos_lifecycle(gate: ApprovalGate, tmp_path: Path) -> None:
    change = gate.request("agent:x", "financeiro:F-001", "lancar", {"valor": 100})
    gate.approve(change.change_id, "tia_may")
    gate.commit(change.change_id, lambda _p: None)

    assert AuditLog(tmp_path / "audit.db").verify_chain() is True


def test_pending_change_imutavel() -> None:
    change = PendingChange("id1", "actor", "res", "desc")

    with pytest.raises(AttributeError):
        change.status = "approved"  # type: ignore[misc]
