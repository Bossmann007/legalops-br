"""SMTP email notifier — envia lembretes de prazos URGENTE via stdlib smtplib.

LGPD: mensagem so contem numero_processo + dies_ad_quem + prazo_efetivo_dias.
Sem nomes, CPFs, OAB, conteudo de ato.

Uso:
    from legalops.email_notifier import EmailNotifier
    n = EmailNotifier("smtp.example.com", 587, "user", "pass", "ops@firma.com")
    n.notify_urgentes(urgent_list, to="advogado@firma.com")
"""

from __future__ import annotations

import smtplib
from datetime import date
from email.message import EmailMessage
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from legalops.orchestrator import ProcessedIntimacao


class EmailNotifierError(RuntimeError):
    """Falha ao enviar e-mail SMTP."""


class EmailNotifier:
    """Cliente SMTP minimo para alertas LegalOps. Plain text body only."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        use_tls: bool = True,
        timeout: float = 10.0,
    ) -> None:
        if not smtp_host:
            raise ValueError("smtp_host obrigatorio")
        if smtp_port <= 0 or smtp_port > 65535:
            raise ValueError(f"smtp_port invalido: {smtp_port}")
        if not from_addr or "@" not in from_addr:
            raise ValueError(f"from_addr invalido: {from_addr!r}")
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.use_tls = use_tls
        self.timeout = timeout

    def notify_urgentes(
        self,
        urgents: list[ProcessedIntimacao],
        to: str,
        subject_prefix: str = "[LegalOps URGENTE]",
        hoje: date | None = None,
    ) -> int:
        """Envia 1 e-mail consolidando urgentes. Retorna count enviado (0 se vazio).

        Raises:
            EmailNotifierError: falha SMTP (connect/auth/send).
        """
        if not to or "@" not in to:
            raise ValueError(f"to invalido: {to!r}")
        if not urgents:
            return 0

        data_str = (hoje or date.today()).isoformat()
        body = self._format_body(urgents, data_str)
        subject = f"{subject_prefix} {len(urgents)} prazo(s) — {data_str}"

        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout) as client:
                client.ehlo()
                if self.use_tls:
                    client.starttls()
                    client.ehlo()
                if self.username:
                    client.login(self.username, self.password)
                client.send_message(msg)
        except (smtplib.SMTPException, OSError) as e:
            raise EmailNotifierError(f"SMTP send failed: {e}") from e

        return len(urgents)

    @staticmethod
    def _format_body(urgents: list[ProcessedIntimacao], data_str: str) -> str:
        """Body plain text. LGPD: so processo + dies_ad_quem + prazo_efetivo_dias."""
        lines = [
            f"PRAZOS URGENTES - {data_str}",
            "",
            f"{len(urgents)} prazo(s) vencendo em <=3 dias uteis:",
            "",
        ]
        for i, r in enumerate(urgents, 1):
            if r.prazo is None:
                continue
            lines.append(
                f"{i}. Processo {r.numero_processo} "
                f"| vence: {r.prazo.dies_ad_quem.isoformat()} "
                f"| prazo efetivo: {r.prazo.prazo_efetivo_dias} dias"
            )
        lines.append("")
        lines.append("-- LegalOps Monitor (nao responder)")
        return "\n".join(lines)
