"""Microsoft 365 / Outlook ingest via Graph API.

OAuth2 client_credentials flow + GET /users/{upn}/mailFolders/{folder}/messages.
Stdlib only (urllib + json + html.parser).

Uso:
    from legalops.m365_ingest import M365Client
    c = M365Client(tenant_id=..., client_id=..., client_secret=...,
                   user_principal_name="adv@firma.com.br")
    emails = c.fetch_recent(folder="Inbox", days=7, sender_filter="tjpr.jus.br")
    urgents = integrate_with_pipeline(emails)

Decisoes:
- Stdlib `urllib` (sem httpx — dep zero)
- Token cache em memoria (re-auth automatico no expiry, margem -30s)
- LGPD: nunca loga body — apenas message_id + sender em erro
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from typing import Any

logger = logging.getLogger(__name__)


class M365Error(RuntimeError):
    """Erro de comunicacao com Microsoft Graph / OAuth."""


@dataclass
class M365Email:
    """Email extraido via Graph API (apenas campos uteis pro pipeline)."""

    message_id: str
    subject: str
    sender: str
    received_at: datetime
    body_text: str
    has_attachments: bool


class _HTMLStripper(HTMLParser):
    """Strip HTML tags into plain text (stdlib only)."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def _strip_html(html: str) -> str:
    """Convert HTML to plain text using stdlib HTMLParser."""
    # Quick path: collapse style/script blocks first
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    parser = _HTMLStripper()
    parser.feed(cleaned)
    text = parser.get_text()
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


class M365Client:
    """Cliente Graph API via OAuth2 client_credentials."""

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"  # noqa: E501, S105
    DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
    HTTP_TIMEOUT = 30

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

    # ---------- internal helpers ----------

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _token_valid(self) -> bool:
        return (
            self._token is not None
            and self._token_expires_at is not None
            and self._now() < self._token_expires_at
        )

    def _authenticate(self) -> str:
        """OAuth2 client_credentials flow.

        Returns:
            access_token. Cache valido ate expiry (-30s margem).
        """
        if self._token_valid():
            assert self._token is not None
            return self._token

        url = self.TOKEN_URL_TEMPLATE.format(tenant=self.tenant_id)
        body = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.DEFAULT_SCOPE,
                "grant_type": "client_credentials",
            }
        ).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.HTTP_TIMEOUT) as resp:  # noqa: S310
                status = resp.status
                raw = resp.read()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:200]
            raise M365Error(f"HTTP {e.code}: {err_body}") from e
        except urllib.error.URLError as e:
            raise M365Error(f"Network error in auth: {e.reason}") from e

        if status != 200:
            raise M365Error(f"HTTP {status}: {raw[:200]!r}")

        payload = json.loads(raw.decode("utf-8"))
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        if not isinstance(token, str) or not token:
            raise M365Error("OAuth response missing access_token")

        self._token = token
        self._token_expires_at = self._now() + timedelta(seconds=expires_in - 30)
        return token

    def _graph_get(self, url: str) -> dict[str, Any]:
        """GET helper com Bearer token + JSON parse."""
        token = self._authenticate()
        req = urllib.request.Request(  # noqa: S310
            url,
            method="GET",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.HTTP_TIMEOUT) as resp:  # noqa: S310
                status = resp.status
                raw = resp.read()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:200]
            raise M365Error(f"HTTP {e.code}: {err_body}") from e
        except urllib.error.URLError as e:
            raise M365Error(f"Network error in graph_get: {e.reason}") from e

        if status != 200:
            raise M365Error(f"HTTP {status}: {raw[:200]!r}")

        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict):
            raise M365Error("Graph response is not a JSON object")
        return result

    # ---------- public API ----------

    def fetch_recent(
        self,
        folder: str = "Inbox",
        days: int = 7,
        sender_filter: str = "",
        max_results: int = 100,
    ) -> list[M365Email]:
        """GET /users/{upn}/mailFolders/{folder}/messages.

        Args:
            folder: nome ou ID do folder (default Inbox)
            days: janela retroativa em dias
            sender_filter: address exato em from/emailAddress/address (eq)
            max_results: limite total (paginacao via @odata.nextLink)

        Returns:
            Lista M365Email pronta pro orchestrator.process_email().
        """
        if not self.user_principal_name:
            raise M365Error("user_principal_name required for fetch_recent")

        since = (self._now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        top = min(100, max_results)

        filters = [f"receivedDateTime ge {since}"]
        if sender_filter:
            filters.append(f"from/emailAddress/address eq '{sender_filter}'")
        filter_expr = " and ".join(filters)

        params = {
            "$top": str(top),
            "$filter": filter_expr,
            "$select": "id,subject,from,receivedDateTime,body,hasAttachments",
        }
        upn = urllib.parse.quote(self.user_principal_name, safe="@")
        folder_q = urllib.parse.quote(folder, safe="")
        url = (
            f"{self.GRAPH_BASE}/users/{upn}/mailFolders/{folder_q}/messages"
            f"?{urllib.parse.urlencode(params)}"
        )

        out: list[M365Email] = []
        next_url: str | None = url
        while next_url and len(out) < max_results:
            payload = self._graph_get(next_url)
            for raw_msg in payload.get("value", []):
                try:
                    out.append(self._convert(raw_msg))
                except (KeyError, ValueError, TypeError) as e:
                    msg_id = (
                        raw_msg.get("id", "<unknown>") if isinstance(raw_msg, dict) else "<unknown>"
                    )
                    logger.warning("skip malformed msg %s: %s", msg_id, e)
                if len(out) >= max_results:
                    break
            next_link = payload.get("@odata.nextLink")
            next_url = next_link if isinstance(next_link, str) else None
        return out

    def fetch_by_id(self, message_id: str) -> M365Email:
        """GET /users/{upn}/messages/{message_id}."""
        if not self.user_principal_name:
            raise M365Error("user_principal_name required for fetch_by_id")
        upn = urllib.parse.quote(self.user_principal_name, safe="@")
        mid = urllib.parse.quote(message_id, safe="")
        url = f"{self.GRAPH_BASE}/users/{upn}/messages/{mid}"
        try:
            payload = self._graph_get(url)
            return self._convert(payload)
        except M365Error:
            logger.exception("fetch_by_id failed", extra={"message_id": message_id})
            raise

    # ---------- conversion ----------

    def _convert(self, raw: dict[str, Any]) -> M365Email:
        """Convert Graph message JSON -> M365Email. LGPD-safe (no body log)."""
        message_id = str(raw["id"])
        subject = str(raw.get("subject", ""))
        from_obj = raw.get("from") or {}
        sender_obj = from_obj.get("emailAddress") if isinstance(from_obj, dict) else None
        sender = str(sender_obj.get("address", "")) if isinstance(sender_obj, dict) else ""

        received_raw = str(raw.get("receivedDateTime", ""))
        try:
            # Graph returns "2026-05-28T12:34:56Z"
            received_at = datetime.fromisoformat(received_raw.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"bad receivedDateTime: {received_raw}") from e

        body_obj = raw.get("body") or {}
        content = str(body_obj.get("content", "")) if isinstance(body_obj, dict) else ""
        ctype = (
            str(body_obj.get("contentType", "text")).lower()
            if isinstance(body_obj, dict)
            else "text"
        )
        body_text = _strip_html(content) if ctype == "html" else content

        return M365Email(
            message_id=message_id,
            subject=subject,
            sender=sender,
            received_at=received_at,
            body_text=body_text,
            has_attachments=bool(raw.get("hasAttachments", False)),
        )


def integrate_with_pipeline(emails: list[M365Email]) -> list[Any]:
    """Pra cada email roda process_email, coleta urgentes, retorna lista.

    Nao notifica — caller decide o que fazer com urgents.
    """
    from legalops.orchestrator import process_email, urgentes

    all_urgents: list[Any] = []
    for em in emails:
        try:
            results = process_email(em.body_text, sender=em.sender)
        except Exception:
            logger.exception(
                "process_email failed",
                extra={"message_id": em.message_id, "sender": em.sender},
            )
            continue
        all_urgents.extend(urgentes(results))
    return all_urgents
