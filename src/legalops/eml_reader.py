"""Leitor de arquivos .eml (RFC 822) — Outlook/Thunderbird export.

Extrai subject, sender, date, body_text. Stdlib email parser apenas
(sem deps externos). Strip HTML basico se nao houver text/plain.

Uso:
    from legalops.eml_reader import read_eml
    content = read_eml(Path("intimacao.eml"))
    print(content.subject, content.date)
    print(content.body_text)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path

MAX_EML_BYTES = 25 * 1024 * 1024  # 25 MB sanity cap


@dataclass(frozen=True)
class EmailContent:
    """Conteudo extraido de um .eml."""

    subject: str
    sender: str
    date: datetime | None
    body_text: str
    attachments_count: int
    source_path: str


def _strip_html(html: str) -> str:
    """Strip basico de tags HTML — fallback quando nao ha text/plain."""
    text = re.sub(
        r"<script[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _extract_body(msg: Message) -> tuple[str, int]:
    """Extrai body text e conta attachments.

    Prefere text/plain. Fallback text/html com strip.
    """
    plain_parts: list[str] = []
    html_parts: list[str] = []
    attachments = 0

    for part in msg.walk():
        ctype = part.get_content_type()
        disp = part.get("Content-Disposition", "")

        if "attachment" in str(disp).lower():
            attachments += 1
            continue

        if part.is_multipart():
            continue

        try:
            content = part.get_content()
        except (LookupError, KeyError):
            payload = part.get_payload(decode=True)
            if isinstance(payload, bytes):
                charset = part.get_content_charset() or "utf-8"
                content = payload.decode(charset, errors="replace")
            else:
                content = str(payload) if payload else ""

        if not isinstance(content, str):
            continue

        if ctype == "text/plain":
            plain_parts.append(content)
        elif ctype == "text/html":
            html_parts.append(content)

    if plain_parts:
        body = "\n".join(plain_parts).strip()
    elif html_parts:
        body = _strip_html("\n".join(html_parts))
    else:
        body = ""

    return body, attachments


def read_eml(path: Path) -> EmailContent:
    """Le um arquivo .eml e retorna EmailContent.

    Args:
        path: caminho para arquivo .eml

    Returns:
        EmailContent com campos extraidos.

    Raises:
        FileNotFoundError: arquivo nao existe
        ValueError: arquivo maior que MAX_EML_BYTES (25MB)
    """
    if not path.exists():
        raise FileNotFoundError(f"EML nao encontrado: {path}")
    if path.stat().st_size > MAX_EML_BYTES:
        raise ValueError(f"EML excede limite {MAX_EML_BYTES} bytes: {path}")

    with path.open("rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    subject = str(msg.get("Subject", "")).strip()
    sender = str(msg.get("From", "")).strip()
    date_hdr = msg.get("Date")
    parsed_date: datetime | None = None
    if date_hdr:
        try:
            parsed_date = parsedate_to_datetime(str(date_hdr))
        except (TypeError, ValueError):
            parsed_date = None

    body, n_att = _extract_body(msg)

    return EmailContent(
        subject=subject,
        sender=sender,
        date=parsed_date,
        body_text=body,
        attachments_count=n_att,
        source_path=str(path),
    )


def read_eml_dir(directory: Path, glob_pattern: str = "*.eml") -> list[EmailContent]:
    """Le todos os .eml em um diretorio (nao recursivo)."""
    if not directory.is_dir():
        raise NotADirectoryError(f"Nao e diretorio: {directory}")
    return [read_eml(p) for p in sorted(directory.glob(glob_pattern))]
