"""WhatsApp notifier — envia lembretes de prazo urgente via bridge.js :3000.

Bridge API: POST /send com body {chatId, message}.

Uso:
    from legalops.whatsapp_notifier import WhatsAppNotifier
    notifier = WhatsAppNotifier(chat_id="5541999999999@s.whatsapp.net")
    notifier.send("Teste de mensagem")

    # Ou integrado com orchestrator:
    notifier.notify_urgentes(processed_results)
"""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING
from urllib import error, request

if TYPE_CHECKING:
    from legalops.orchestrator import ProcessedIntimacao


DEFAULT_BRIDGE_URL = "http://localhost:3000"
DEFAULT_TIMEOUT = 10.0


class WhatsAppNotifierError(Exception):
    """Falha ao enviar mensagem WhatsApp."""


class WhatsAppNotifier:
    """Cliente HTTP para bridge.js WhatsApp gateway."""

    def __init__(
        self,
        chat_id: str,
        base_url: str = DEFAULT_BRIDGE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not chat_id:
            raise ValueError("chat_id obrigatorio")
        self.chat_id = chat_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def send(self, message: str) -> dict[str, object]:
        """POST /send {chatId, message}. Retorna response JSON.

        Raises:
            WhatsAppNotifierError: bridge offline, HTTP != 2xx, ou JSON invalido.
        """
        if not message:
            raise ValueError("message vazia")

        url = f"{self.base_url}/send"
        payload = json.dumps(
            {"chatId": self.chat_id, "message": message}, ensure_ascii=False
        ).encode("utf-8")

        req = request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                status = resp.status
                body = resp.read().decode("utf-8")
        except error.URLError as e:
            raise WhatsAppNotifierError(f"Bridge unreachable: {e}") from e
        except TimeoutError as e:
            raise WhatsAppNotifierError(f"Bridge timeout: {e}") from e

        if status >= 400:
            raise WhatsAppNotifierError(f"HTTP {status}: {body[:200]}")

        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError:
            return {"raw": body}

    def notify_urgentes(
        self,
        results: list[ProcessedIntimacao],
        hoje: date | None = None,
    ) -> str | None:
        """Formata e envia lembrete WhatsApp de prazos URGENTE (<= 3 dias).

        Returns:
            Mensagem enviada (string) ou None se nenhum urgente.
        """
        urgent = [
            r
            for r in results
            if r.prazo is not None and r.prazo.alerta == "URGENTE"
        ]
        if not urgent:
            return None

        msg = self.format_urgentes_message(urgent, hoje=hoje)
        self.send(msg)
        return msg

    @staticmethod
    def format_urgentes_message(
        urgent: list[ProcessedIntimacao],
        hoje: date | None = None,
    ) -> str:
        """Formata mensagem WhatsApp pra prazos urgentes. Sem PII."""
        data_str = (hoje or date.today()).isoformat()
        lines = [
            f"🚨 PRAZOS URGENTES — {data_str}",
            "",
            f"⚠️ {len(urgent)} prazo(s) vencendo em ≤3 dias úteis:",
            "",
        ]
        for i, r in enumerate(urgent, 1):
            if r.prazo is None:
                continue
            lines.append(f"{i}. Proc {r.numero_processo}")
            lines.append(f"   • Ato: {r.parsed.tipo_ato}")
            lines.append(
                f"   • Vence: {r.prazo.dies_ad_quem.isoformat()} "
                f"({r.prazo.dias_uteis_restantes_hoje} dias úteis)"
            )
            lines.append("")
        lines.append("— LegalOps Monitor (não responder)")
        return "\n".join(lines)
