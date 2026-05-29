"""Testes do renewal_watcher (Renewal Watcher — fase v1.2)."""

from __future__ import annotations

from datetime import date

from legalops.renewal_watcher import Contrato, RenewalWatcher


def _contrato(cid: str, fim: date, aviso: int = 0, auto: bool = False) -> Contrato:
    return Contrato(cid, f"Contrato {cid}", date(2026, 1, 1), fim, aviso, auto)


def test_add_e_lista() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 12, 31)))
    assert len(w.contratos()) == 1


def test_remove() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 12, 31)))
    w.remove("c1")
    assert w.contratos() == []


def test_vencido() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 5, 1)))
    alertas = w.check(hoje=date(2026, 5, 20))
    assert alertas[0].urgencia == "vencido"


def test_critico() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 6, 1)))
    alertas = w.check(hoje=date(2026, 5, 20))
    assert alertas[0].urgencia == "critico"


def test_atencao() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 6, 30)))
    alertas = w.check(hoje=date(2026, 5, 20))
    assert alertas[0].urgencia == "atencao"


def test_ok_excluido_por_padrao() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 12, 31)))
    alertas = w.check(hoje=date(2026, 5, 20))
    assert alertas == []


def test_ok_incluido_quando_pedido() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 12, 31)))
    alertas = w.check(hoje=date(2026, 5, 20), incluir_ok=True)
    assert alertas[0].urgencia == "ok"


def test_aviso_previo_antecipa_urgencia() -> None:
    # Vencimento longe (60d), mas aviso previo de 90d ja venceu -> critico/vencido.
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 7, 19), aviso=90))
    alertas = w.check(hoje=date(2026, 5, 20), incluir_ok=True)
    assert alertas[0].urgencia == "vencido"


def test_dias_para_aviso_calculado() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 6, 30), aviso=30))
    alerta = w.check(hoje=date(2026, 5, 20), incluir_ok=True)[0]
    assert alerta.dias_para_aviso == (date(2026, 5, 31) - date(2026, 5, 20)).days


def test_dias_para_aviso_none_sem_aviso() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 6, 30)))
    alerta = w.check(hoje=date(2026, 5, 20), incluir_ok=True)[0]
    assert alerta.dias_para_aviso is None


def test_ordenacao_por_urgencia() -> None:
    w = RenewalWatcher()
    w.add(_contrato("ok", date(2026, 12, 31)))
    w.add(_contrato("venc", date(2026, 5, 1)))
    w.add(_contrato("crit", date(2026, 6, 1)))
    alertas = w.check(hoje=date(2026, 5, 20), incluir_ok=True)
    assert [a.contrato_id for a in alertas] == ["venc", "crit", "ok"]


def test_renovacao_automatica_propagada() -> None:
    w = RenewalWatcher()
    w.add(_contrato("c1", date(2026, 6, 1), auto=True))
    alerta = w.check(hoje=date(2026, 5, 20))[0]
    assert alerta.renovacao_automatica is True
