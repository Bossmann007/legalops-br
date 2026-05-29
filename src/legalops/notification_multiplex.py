"""Multiplex de notificacoes — orquestra varios canais (WhatsApp/Email/Slack).

Features:
- Threshold: filtra urgentes com prazo_efetivo_dias < min_prazo_dias.
- Quiet hours: janela [start, end] em que tudo eh suprimido.
- Resiliencia: falha de um canal nao quebra outros (loga e segue).

Uso:
    mux = NotificationMultiplex(min_prazo_dias=3)
    mux.add_channel("whatsapp", lambda u, h: wa.notify_urgentes(u, hoje=h) and len(u) or 0)
    mux.add_channel("email", lambda u, h: em.notify_urgentes(u, to="x@y.com", hoje=h))
    counts = mux.notify_all(urgents, hoje=date.today())
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime, time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from legalops.orchestrator import ProcessedIntimacao


NotifierCallable = Callable[[list["ProcessedIntimacao"], "date | None"], int]

_log = logging.getLogger(__name__)


class NotificationMultiplex:
    """Fan-out para multiplos canais com threshold + quiet hours."""

    def __init__(
        self,
        min_prazo_dias: int = 3,
        quiet_hours_start: time | None = None,
        quiet_hours_end: time | None = None,
    ) -> None:
        if min_prazo_dias < 0:
            raise ValueError(f"min_prazo_dias deve ser >=0: {min_prazo_dias}")
        self.min_prazo_dias = min_prazo_dias
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
        self._channels: list[tuple[str, NotifierCallable]] = []

    def add_channel(self, name: str, notifier_callable: NotifierCallable) -> None:
        """Registra um canal pelo nome."""
        if not name:
            raise ValueError("nome do canal obrigatorio")
        self._channels.append((name, notifier_callable))

    @property
    def channels(self) -> list[str]:
        return [n for n, _ in self._channels]

    def _in_quiet_hours(self, now: time) -> bool:
        s, e = self.quiet_hours_start, self.quiet_hours_end
        if s is None or e is None:
            return False
        if s <= e:
            return s <= now < e
        # janela cruza meia-noite (ex: 22:00 -> 06:00)
        return now >= s or now < e

    def _filter(self, urgents: list[ProcessedIntimacao]) -> list[ProcessedIntimacao]:
        out: list[ProcessedIntimacao] = []
        for r in urgents:
            if r.prazo is None:
                continue
            # Threshold: incluir somente prazos com prazo_efetivo_dias <= min_prazo_dias
            # (i.e., os mais urgentes). Spec: "filter urgents below min_prazo_dias" =
            # filtrar OUT aqueles com prazo > min_prazo_dias.
            if r.prazo.prazo_efetivo_dias > self.min_prazo_dias:
                continue
            out.append(r)
        return out

    def notify_all(
        self,
        urgents: list[ProcessedIntimacao],
        hoje: date | None = None,
    ) -> dict[str, int]:
        """Dispara para todos canais. Retorna {channel: count_sent}."""
        now = datetime.now().time()
        if self._in_quiet_hours(now):
            _log.info("multiplex: quiet hours active, skipping all channels")
            return {}

        filtered = self._filter(urgents)
        result: dict[str, int] = {}
        for name, fn in self._channels:
            try:
                result[name] = int(fn(filtered, hoje))
            except Exception as e:  # noqa: BLE001 - per-channel isolation
                _log.error("multiplex: channel %r failed: %s", name, e)
                result[name] = 0
        return result
