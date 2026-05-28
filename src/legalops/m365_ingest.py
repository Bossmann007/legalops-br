"""Microsoft 365 / Outlook ingest stub (Graph API).

STATUS: stub — define interface, nao chama Graph ainda. Auth + paginacao
implementadas via OAuth client_credentials quando credenciais forem providas.

Uso futuro:
    from legalops.m365_ingest import M365Client
    c = M365Client(tenant_id=..., client_id=..., client_secret=...)
    emails = c.fetch_recent(folder="Inbox", days=7, sender_filter="@tjpr.jus.br")

Decisao de arquitetura:
- Stdlib `urllib` apenas (sem httpx — manter dep zero)
- Token cache em memoria (re-auth automatico no expiry)
- Nao persiste corpo do email — passa direto pro pipeline
- LGPD: usuario fornece tenant_id (escopo controlado), filtra por sender
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class M365Email:
    """Email extraido via Graph API (apenas campos uteis pro pipeline)."""

    message_id: str
    subject: str
    sender: str
    received_at: datetime
    body_text: str
    has_attachments: bool


class M365Client:
    """Cliente Graph API — STUB. Implementacao real via urllib + OAuth2."""

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"  # noqa: E501, S105

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        user_principal_name: str = "",
    ) -> None:
        """Args:
        tenant_id: Azure AD tenant ID
        client_id: app registration client ID
        client_secret: app registration secret (rotacionar — nao commit)
        user_principal_name: UPN do mailbox a consultar (admin consent required)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_principal_name = user_principal_name
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    def _authenticate(self) -> str:
        """STUB: OAuth2 client_credentials flow.

        Retorna access_token. Cache ate expiry (-30s margem).
        """
        raise NotImplementedError(
            "M365 OAuth — implementar com urllib.request + grant_type=client_credentials"
        )

    def fetch_recent(
        self,
        folder: str = "Inbox",
        days: int = 7,
        sender_filter: str = "",
        max_results: int = 100,
    ) -> list[M365Email]:
        """STUB: GET /users/{upn}/mailFolders/{folder}/messages.

        Args:
            folder: nome ou ID do folder (default Inbox)
            days: janela retroativa em dias
            sender_filter: substring no campo from.emailAddress.address
            max_results: limite paginacao

        Returns:
            Lista M365Email pronta pro orchestrator.process_email().
        """
        raise NotImplementedError(
            "M365 fetch — implementar GET messages com $filter receivedDateTime + $top + paginacao"
        )

    def fetch_by_id(self, message_id: str) -> M365Email:
        """STUB: GET /users/{upn}/messages/{message_id}."""
        raise NotImplementedError("M365 fetch_by_id — implementar")


def integrate_with_pipeline(emails: list[M365Email]) -> None:
    """Helper: pra cada email rodar process_email + audit log.

    Stub — implementacao depende de M365Client funcional.
    """
    raise NotImplementedError(
        "Aguardando M365Client funcional. Estrutura:\n"
        "  for em in emails:\n"
        "      results = process_email(em.body_text, sender=em.sender)\n"
        "      for r in urgentes(results):\n"
        "          notifier.notify_urgentes([r])\n"
    )
