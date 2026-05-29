"""Feeds reader stub for BACEN and CVM RSS-like feeds.

Parses RSS 2.0 subset XML for jurisprudencia bancaria / normas relevantes.
STUB version: parses synthetic feed text only; no network calls.

Security:
    - Uses only stdlib xml.etree.ElementTree (no lxml, no XXE risk).
    - Rejects feeds larger than MAX_FEED_BYTES (10 MB) defensively.
    - Truncates summary to MAX_SUMMARY_CHARS to bound memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Literal
from xml.etree import ElementTree as ET

Source = Literal["BACEN", "CVM"]

MAX_FEED_BYTES: int = 10 * 1024 * 1024  # 10 MB
MAX_SUMMARY_CHARS: int = 500


@dataclass(frozen=True)
class FeedItem:
    """A single normalized RSS feed entry."""

    source: Source
    title: str
    summary: str
    published_date: date
    url: str
    categories: tuple[str, ...]


KEYWORDS_BANCARIO_DEFAULT: tuple[str, ...] = (
    "consumidor",
    "juros abusivos",
    "capitalizacao",
    "spread",
    "tarifa",
    "CDC",
    "abusividade",
    "credito consignado",
    "financiamento veiculo",
)


def _parse_pub_date(raw: str) -> date:
    """Parse RFC 822 pubDate, falling back to ISO YYYY-MM-DD."""
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            return dt.date()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Unparseable pubDate: {raw!r}") from e


def parse_feed_xml(xml_text: str, source: Source) -> list[FeedItem]:
    """Parse RSS 2.0 subset XML text into a list of ``FeedItem``.

    Args:
        xml_text: Raw XML string.
        source: Either ``"BACEN"`` or ``"CVM"`` (assigned to every item).

    Returns:
        List of ``FeedItem`` in source order. Empty list for feed with no items.

    Raises:
        ValueError: If feed exceeds ``MAX_FEED_BYTES`` or XML is malformed.
    """
    if len(xml_text.encode("utf-8")) > MAX_FEED_BYTES:
        raise ValueError(f"Feed exceeds {MAX_FEED_BYTES} bytes (defensive limit)")

    try:
        # S314: este parser recebe `xml_text` como argumento — nao faz fetch
        # remoto. CPython >= 3.7.1 desabilita external entity resolution em
        # `xml.etree.ElementTree.fromstring` por default (sem `XMLParser`
        # customizado), entao XXE classico nao se aplica. MAX_FEED_BYTES corta
        # billion-laughs antes do parse. Quando passar a aceitar feeds remotos
        # nao confiaveis (v0.3+): trocar pra `defusedxml.ElementTree.fromstring`.
        root = ET.fromstring(xml_text)  # noqa: S314
    except ET.ParseError as e:
        raise ValueError(f"Malformed XML: {e}") from e

    items_xml = root.findall(".//item")

    results: list[FeedItem] = []
    for item in items_xml:
        title_el = item.find("title")
        desc_el = item.find("description")
        pub_el = item.find("pubDate")
        link_el = item.find("link")
        cat_els = item.findall("category")

        title = (title_el.text or "").strip() if title_el is not None else ""
        summary_raw = (desc_el.text or "").strip() if desc_el is not None else ""
        summary = summary_raw[:MAX_SUMMARY_CHARS]
        url = (link_el.text or "").strip() if link_el is not None else ""

        if pub_el is None or not (pub_el.text or "").strip():
            raise ValueError("Missing required <pubDate> in item")
        published = _parse_pub_date(pub_el.text or "")

        categories = tuple((c.text or "").strip() for c in cat_els if (c.text or "").strip())

        results.append(
            FeedItem(
                source=source,
                title=title,
                summary=summary,
                published_date=published,
                url=url,
                categories=categories,
            )
        )

    return results


def filter_by_keywords(items: list[FeedItem], keywords: list[str]) -> list[FeedItem]:
    """Return items whose title OR summary contains any keyword (case-insensitive)."""
    lowered = [k.lower() for k in keywords if k]
    if not lowered:
        return []
    out: list[FeedItem] = []
    for it in items:
        hay = f"{it.title}\n{it.summary}".lower()
        if any(k in hay for k in lowered):
            out.append(it)
    return out


def filter_by_date_range(items: list[FeedItem], start: date, end: date) -> list[FeedItem]:
    """Return items with ``start <= published_date <= end``."""
    if start > end:
        raise ValueError("start must be <= end")
    return [it for it in items if start <= it.published_date <= end]
