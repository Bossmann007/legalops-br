"""Tests slack_notifier — urlopen mockado."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock, patch
from urllib import error

import pytest

from legalops.cpc_prazos import PrazoInput, calcular_prazo
from legalops.orchestrator import ProcessedIntimacao
from legalops.slack_notifier import SlackNotifier, SlackNotifierError
from legalops.tjpr_parser import Intimacao

WEBHOOK = "https://hooks.slack.com/services/T/B/X"


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


def _mock_resp(status: int = 200, body: bytes = b"ok") -> MagicMock:
    m = MagicMock()
    m.status = status
    m.read.return_value = body
    m.__enter__ = lambda self: self
    m.__exit__ = lambda *a: None
    return m


class TestInit:
    def test_ok(self) -> None:
        n = SlackNotifier(WEBHOOK)
        assert n.channel == ""

    def test_bad_scheme(self) -> None:
        with pytest.raises(ValueError):
            SlackNotifier("ftp://x.com/")

    def test_empty_url(self) -> None:
        with pytest.raises(ValueError):
            SlackNotifier("")

    def test_no_netloc(self) -> None:
        with pytest.raises(ValueError):
            SlackNotifier("http://")


class TestNotify:
    def test_empty_returns_zero(self) -> None:
        n = SlackNotifier(WEBHOOK)
        with patch("legalops.slack_notifier.request.urlopen") as mock_open:
            assert n.notify_urgentes([]) == 0
            mock_open.assert_not_called()

    def test_sends_text_only(self) -> None:
        n = SlackNotifier(WEBHOOK)
        u = [_proc("A", 1, date(2025, 5, 5))]
        with patch(
            "legalops.slack_notifier.request.urlopen", return_value=_mock_resp()
        ) as mock_open:
            count = n.notify_urgentes(u, hoje=date(2025, 5, 5))
        assert count == 1
        req = mock_open.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert "text" in payload
        assert "channel" not in payload

    def test_sends_with_channel(self) -> None:
        n = SlackNotifier(WEBHOOK, channel="#prazos")
        u = [_proc("A", 1, date(2025, 5, 5))]
        with patch(
            "legalops.slack_notifier.request.urlopen", return_value=_mock_resp()
        ) as mock_open:
            n.notify_urgentes(u)
        payload = json.loads(mock_open.call_args[0][0].data.decode("utf-8"))
        assert payload["channel"] == "#prazos"

    def test_http_error_raises(self) -> None:
        n = SlackNotifier(WEBHOOK)
        u = [_proc("A", 1, date(2025, 5, 5))]
        with patch("legalops.slack_notifier.request.urlopen", return_value=_mock_resp(status=500)):
            with pytest.raises(SlackNotifierError):
                n.notify_urgentes(u)

    def test_urlerror_raises(self) -> None:
        n = SlackNotifier(WEBHOOK)
        u = [_proc("A", 1, date(2025, 5, 5))]
        with patch(
            "legalops.slack_notifier.request.urlopen",
            side_effect=error.URLError("boom"),
        ):
            with pytest.raises(SlackNotifierError):
                n.notify_urgentes(u)

    def test_timeout_raises(self) -> None:
        n = SlackNotifier(WEBHOOK)
        u = [_proc("A", 1, date(2025, 5, 5))]
        with patch("legalops.slack_notifier.request.urlopen", side_effect=TimeoutError("t")):
            with pytest.raises(SlackNotifierError):
                n.notify_urgentes(u)

    def test_text_format_no_pii(self) -> None:
        n = SlackNotifier(WEBHOOK)
        u = [_proc("0001234-56.2024.8.16.0001", 1, date(2025, 5, 5))]
        with patch(
            "legalops.slack_notifier.request.urlopen", return_value=_mock_resp()
        ) as mock_open:
            n.notify_urgentes(u, hoje=date(2025, 5, 5))
        payload = json.loads(mock_open.call_args[0][0].data.decode("utf-8"))
        text = payload["text"]
        assert "0001234-56.2024.8.16.0001" in text
        assert "CPF" not in text

    def test_post_method(self) -> None:
        n = SlackNotifier(WEBHOOK)
        u = [_proc("A", 1, date(2025, 5, 5))]
        with patch(
            "legalops.slack_notifier.request.urlopen", return_value=_mock_resp()
        ) as mock_open:
            n.notify_urgentes(u)
        req = mock_open.call_args[0][0]
        assert req.get_method() == "POST"
        assert req.headers["Content-type"] == "application/json"
