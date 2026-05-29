"""Tests notification_multiplex — fan-out + threshold + quiet hours."""

from __future__ import annotations

from datetime import date, datetime, time
from unittest.mock import patch

import pytest

from legalops.cpc_prazos import PrazoInput, calcular_prazo
from legalops.notification_multiplex import NotificationMultiplex
from legalops.orchestrator import ProcessedIntimacao
from legalops.tjpr_parser import Intimacao


def _proc(num: str, prazo_dias: int, hoje: date) -> ProcessedIntimacao:
    parsed = Intimacao(
        numero_processo=num,
        data_publicacao=hoje,
        prazo_dias=prazo_dias,
        tipo_ato="despacho",
    )
    p = calcular_prazo(
        PrazoInput(data_publicacao=hoje, prazo_dias=prazo_dias, parte="particular"),
        hoje=hoje,
    )
    return ProcessedIntimacao(
        numero_processo=num, redacted_text="", pii_matches=0, parsed=parsed, prazo=p
    )


class TestInit:
    def test_default(self) -> None:
        m = NotificationMultiplex()
        assert m.min_prazo_dias == 3
        assert m.channels == []

    def test_bad_min_prazo(self) -> None:
        with pytest.raises(ValueError):
            NotificationMultiplex(min_prazo_dias=-1)

    def test_add_channel_requires_name(self) -> None:
        m = NotificationMultiplex()
        with pytest.raises(ValueError):
            m.add_channel("", lambda u, h: 0)


class TestNotifyAll:
    def test_empty_urgents(self) -> None:
        m = NotificationMultiplex()
        calls: list[int] = []
        m.add_channel("x", lambda u, h: calls.append(len(u)) or 0)
        out = m.notify_all([], hoje=date(2025, 5, 5))
        # canal eh chamado mas com lista filtrada (vazia)
        assert out == {"x": 0}
        assert calls == [0]

    def test_fanout_multiple(self) -> None:
        m = NotificationMultiplex(min_prazo_dias=15)
        u = [_proc("A", 1, date(2025, 5, 5))]
        m.add_channel("a", lambda urg, h: len(urg))
        m.add_channel("b", lambda urg, h: len(urg) * 2)
        out = m.notify_all(u)
        assert out == {"a": 1, "b": 2}

    def test_per_channel_error_isolated(self) -> None:
        m = NotificationMultiplex(min_prazo_dias=15)
        u = [_proc("A", 1, date(2025, 5, 5))]

        def _bad(urg: list, h: date | None) -> int:
            raise RuntimeError("boom")

        m.add_channel("ok", lambda urg, h: 1)
        m.add_channel("bad", _bad)
        out = m.notify_all(u)
        assert out["ok"] == 1
        assert out["bad"] == 0

    def test_threshold_filters_high_prazo(self) -> None:
        # prazo_efetivo_dias = 15 (>3 default) -> filtrado out
        m = NotificationMultiplex(min_prazo_dias=3)
        u = [_proc("A", 15, date(2025, 5, 5))]
        captured: list[int] = []
        m.add_channel("x", lambda urg, h: captured.append(len(urg)) or len(urg))
        out = m.notify_all(u)
        assert captured == [0]
        assert out == {"x": 0}

    def test_threshold_keeps_low_prazo(self) -> None:
        m = NotificationMultiplex(min_prazo_dias=3)
        u = [_proc("A", 2, date(2025, 5, 5))]
        captured: list[int] = []
        m.add_channel("x", lambda urg, h: captured.append(len(urg)) or len(urg))
        m.notify_all(u)
        assert captured == [1]

    def test_quiet_hours_skip(self) -> None:
        m = NotificationMultiplex(
            min_prazo_dias=15,
            quiet_hours_start=time(0, 0),
            quiet_hours_end=time(23, 59),
        )
        u = [_proc("A", 1, date(2025, 5, 5))]
        called: list[int] = []
        m.add_channel("x", lambda urg, h: called.append(1) or 1)

        fake_now = datetime(2025, 5, 5, 12, 0, 0)
        with patch("legalops.notification_multiplex.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            out = m.notify_all(u)
        assert out == {}
        assert called == []

    def test_quiet_hours_cross_midnight(self) -> None:
        # janela 22:00 -> 06:00
        m = NotificationMultiplex(
            min_prazo_dias=15,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(6, 0),
        )
        u = [_proc("A", 1, date(2025, 5, 5))]
        m.add_channel("x", lambda urg, h: 1)

        # 23:00 deve silenciar
        fake_now = datetime(2025, 5, 5, 23, 0, 0)
        with patch("legalops.notification_multiplex.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            assert m.notify_all(u) == {}

        # 12:00 deve disparar
        fake_now2 = datetime(2025, 5, 5, 12, 0, 0)
        with patch("legalops.notification_multiplex.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now2
            assert m.notify_all(u) == {"x": 1}

    def test_no_quiet_hours_means_always_active(self) -> None:
        m = NotificationMultiplex(min_prazo_dias=15)
        u = [_proc("A", 1, date(2025, 5, 5))]
        m.add_channel("x", lambda urg, h: 1)
        # qualquer hora dispara
        assert m.notify_all(u) == {"x": 1}
