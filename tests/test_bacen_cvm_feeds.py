"""Tests for legalops.bacen_cvm_feeds.

Malformed XML contract: parse_feed_xml raises ValueError (wraps ET.ParseError).
"""

from __future__ import annotations

from datetime import date

import pytest

from legalops.bacen_cvm_feeds import (
    KEYWORDS_BANCARIO_DEFAULT,
    FeedItem,
    filter_by_date_range,
    filter_by_keywords,
    parse_feed_xml,
)

SIMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BACEN Normativos</title>
    <item>
      <title>Circular 4.000: tarifas bancarias</title>
      <description>Nova regra sobre tarifa e abusividade ao consumidor.</description>
      <pubDate>Wed, 21 May 2026 10:00:00 GMT</pubDate>
      <link>https://example.bacen.gov.br/circ/4000</link>
      <category>circular</category>
      <category>consumidor</category>
    </item>
  </channel>
</rss>
"""

THREE_ITEM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Item A sobre juros abusivos</title>
      <description>Detalhes de spread elevado.</description>
      <pubDate>Mon, 04 May 2026 09:00:00 GMT</pubDate>
      <link>https://example.bacen.gov.br/a</link>
      <category>juros</category>
    </item>
    <item>
      <title>Item B sobre CDC</title>
      <description>Norma envolvendo capitalizacao de juros.</description>
      <pubDate>Wed, 13 May 2026 09:00:00 GMT</pubDate>
      <link>https://example.bacen.gov.br/b</link>
      <category>consumidor</category>
    </item>
    <item>
      <title>Item C generico</title>
      <description>Nota administrativa de protocolo.</description>
      <pubDate>Fri, 22 May 2026 09:00:00 GMT</pubDate>
      <link>https://example.bacen.gov.br/c</link>
      <category>administrativo</category>
    </item>
  </channel>
</rss>
"""

EMPTY_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>vazio</title></channel></rss>
"""

CVM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Resolucao CVM 100</title>
      <description>Mercado de valores mobiliarios.</description>
      <pubDate>Tue, 10 Feb 2026 08:00:00 GMT</pubDate>
      <link>https://example.cvm.gov.br/100</link>
      <category>resolucao</category>
    </item>
  </channel>
</rss>
"""

MALFORMED_FEED = "<rss><channel><item><title>missing close"


def test_parse_simple_feed_single_item() -> None:
    items = parse_feed_xml(SIMPLE_FEED, "BACEN")
    assert len(items) == 1
    it = items[0]
    assert isinstance(it, FeedItem)
    assert it.source == "BACEN"
    assert it.title == "Circular 4.000: tarifas bancarias"
    assert "tarifa" in it.summary
    assert it.published_date == date(2026, 5, 21)
    assert it.url == "https://example.bacen.gov.br/circ/4000"
    assert it.categories == ("circular", "consumidor")


def test_parse_feed_three_items() -> None:
    items = parse_feed_xml(THREE_ITEM_FEED, "BACEN")
    assert len(items) == 3
    assert [i.title for i in items] == [
        "Item A sobre juros abusivos",
        "Item B sobre CDC",
        "Item C generico",
    ]


def test_parse_handles_multiple_categories() -> None:
    items = parse_feed_xml(SIMPLE_FEED, "BACEN")
    assert items[0].categories == ("circular", "consumidor")
    assert isinstance(items[0].categories, tuple)


def test_empty_feed_returns_empty_list() -> None:
    assert parse_feed_xml(EMPTY_FEED, "BACEN") == []


def test_malformed_xml_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse_feed_xml(MALFORMED_FEED, "BACEN")


def test_source_attribution_bacen() -> None:
    items = parse_feed_xml(SIMPLE_FEED, "BACEN")
    assert all(i.source == "BACEN" for i in items)


def test_source_attribution_cvm() -> None:
    items = parse_feed_xml(CVM_FEED, "CVM")
    assert len(items) == 1
    assert items[0].source == "CVM"
    assert items[0].title == "Resolucao CVM 100"


def test_filter_by_keywords_case_insensitive() -> None:
    items = parse_feed_xml(THREE_ITEM_FEED, "BACEN")
    out = filter_by_keywords(items, ["JUROS ABUSIVOS"])
    assert len(out) == 1
    assert out[0].title == "Item A sobre juros abusivos"


def test_filter_by_keywords_matches_title_or_summary() -> None:
    items = parse_feed_xml(THREE_ITEM_FEED, "BACEN")

    out_title = filter_by_keywords(items, ["CDC"])
    assert [i.title for i in out_title] == ["Item B sobre CDC"]

    out_summary = filter_by_keywords(items, ["capitalizacao"])
    assert [i.title for i in out_summary] == ["Item B sobre CDC"]

    out_none = filter_by_keywords(items, ["inexistente_xyz"])
    assert out_none == []


def test_filter_by_keywords_empty_list_returns_empty() -> None:
    items = parse_feed_xml(THREE_ITEM_FEED, "BACEN")
    assert filter_by_keywords(items, []) == []


def test_filter_by_date_range_inclusive_bounds() -> None:
    items = parse_feed_xml(THREE_ITEM_FEED, "BACEN")

    # Inclusive on both ends: 2026-05-04 .. 2026-05-22 -> all 3 items
    all_in = filter_by_date_range(items, date(2026, 5, 4), date(2026, 5, 22))
    assert len(all_in) == 3

    # Tight to just the middle item
    mid = filter_by_date_range(items, date(2026, 5, 13), date(2026, 5, 13))
    assert len(mid) == 1
    assert mid[0].title == "Item B sobre CDC"

    # Excludes everything
    none_in = filter_by_date_range(items, date(2027, 1, 1), date(2027, 12, 31))
    assert none_in == []


def test_filter_by_date_range_rejects_inverted_range() -> None:
    items = parse_feed_xml(THREE_ITEM_FEED, "BACEN")
    with pytest.raises(ValueError):
        filter_by_date_range(items, date(2026, 12, 31), date(2026, 1, 1))


def test_keywords_default_non_empty_tuple() -> None:
    assert isinstance(KEYWORDS_BANCARIO_DEFAULT, tuple)
    assert len(KEYWORDS_BANCARIO_DEFAULT) > 0
    assert all(isinstance(k, str) and k for k in KEYWORDS_BANCARIO_DEFAULT)
