"""Slack incoming-webhook notifier — POST JSON {text, channel?}.

LGPD: mensagem so contem processo + dies_ad_quem. Sem PII.

Uso:
    from legalops.slack_notifier import SlackNotifier
    n = SlackNotifier("https://hooks.slack.com/services/T/B/X")
    n.notify_urgentes(urgent_list)
"""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING
from urllib import error, parse, request

if TYPE_CHECKING:
    from legalops.orchestrator import ProcessedIntimacao


class SlackNotifierError(RuntimeError):
    """Falha ao enviar mensagem Slack."""


class SlackNotifier:
    """Cliente Slack incoming webhook."""

    def __init__(
        self,
        webhook_url: str,
        channel: str = "",
        timeout: float = 10.0,
    ) -> None:
        if not webhook_url:
            raise ValueError("webhook_url obrigatorio")
        parsed = parse.urlparse(webhook_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"webhook_url scheme invalido: {parsed.scheme!r}")
        if not parsed.netloc:
            raise ValueError(f"webhook_url sem host: {webhook_url!r}")
        self.webhook_url = webhook_url
        self.channel = channel
        self.timeout = timeout

    def notify_urgentes(
        self,
        urgents: list[ProcessedIntimacao],
        hoje: date | None = None,
    ) -> int:
        """POST {text, channel?} no webhook. Retorna count (0 se vazio).

        Raises:
            SlackNotifierError: falha HTTP/network.
        """
        if not urgents:
            return 0

        data_str = (hoje or date.today()).isoformat()
        text = self._format_text(urgents, data_str)
        payload: dict[str, str] = {"text": text}
        if self.channel:
            payload["channel"] = self.channel

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        # S310: webhook_url scheme validado em __init__.
        req = request.Request(  # noqa: S310
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                status = resp.status
                resp_body = resp.read().decode("utf-8", errors="replace")
        except error.URLError as e:
            raise SlackNotifierError(f"Slack unreachable: {e}") from e
        except TimeoutError as e:
            raise SlackNotifierError(f"Slack timeout: {e}") from e

        if status >= 400:
            raise SlackNotifierError(f"HTTP {status}: {resp_body[:200]}")

        return len(urgents)

    @staticmethod
    def _format_text(urgents: list[ProcessedIntimacao], data_str: str) -> str:
        """Plain text. LGPD: so processo + dies_ad_quem."""
        lines = [
            f"*PRAZOS URGENTES* — {data_str}",
            f"{len(urgents)} prazo(s) vencendo em <=3 dias uteis:",
        ]
        for i, r in enumerate(urgents, 1):
            if r.prazo is None:
                continue
            lines.append(
                f"{i}. Proc {r.numero_processo} — vence {r.prazo.dies_ad_quem.isoformat()}"
            )
        return "\n".join(lines)
