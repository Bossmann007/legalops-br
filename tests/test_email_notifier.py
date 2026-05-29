"""Tests email_notifier — smtplib mockado."""

from __future__ import annotations

import smtplib
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from legalops.cpc_prazos import PrazoInput, calcular_prazo
from legalops.email_notifier import EmailNotifier, EmailNotifierError
from legalops.orchestrator import ProcessedIntimacao
from legalops.tjpr_parser import Intimacao


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


def _mk_client() -> MagicMock:
    m = MagicMock()
    m.__enter__ = lambda self: self
    m.__exit__ = lambda *a: None
    return m


def _notifier() -> EmailNotifier:
    return EmailNotifier(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="u",
        password="p",  # noqa: S106
        from_addr="from@example.com",
    )


class TestInit:
    def test_ok(self) -> None:
        n = _notifier()
        assert n.smtp_host == "smtp.example.com"
        assert n.use_tls is True

    def test_bad_host(self) -> None:
        with pytest.raises(ValueError):
            EmailNotifier("", 587, "u", "p", "x@y.com")

    def test_bad_port(self) -> None:
        with pytest.raises(ValueError):
            EmailNotifier("h", 0, "u", "p", "x@y.com")

    def test_bad_port_high(self) -> None:
        with pytest.raises(ValueError):
            EmailNotifier("h", 99999, "u", "p", "x@y.com")

    def test_bad_from_addr(self) -> None:
        with pytest.raises(ValueError):
            EmailNotifier("h", 25, "u", "p", "no-at-sign")


class TestNotifyUrgentes:
    def test_empty_returns_zero(self) -> None:
        n = _notifier()
        with patch("smtplib.SMTP") as mock_smtp:
            assert n.notify_urgentes([], to="x@y.com") == 0
            mock_smtp.assert_not_called()

    def test_bad_to(self) -> None:
        n = _notifier()
        with pytest.raises(ValueError):
            n.notify_urgentes([_proc("1", 1, date(2025, 5, 5))], to="invalid")

    def test_sends_and_returns_count(self) -> None:
        n = _notifier()
        u = [_proc("0001234-56.2024.8.16.0001", 1, date(2025, 5, 5))]
        client = _mk_client()
        with patch("smtplib.SMTP", return_value=client) as mock_smtp:
            count = n.notify_urgentes(u, to="adv@firma.com", hoje=date(2025, 5, 5))
        assert count == 1
        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=10.0)
        client.starttls.assert_called_once()
        client.login.assert_called_once_with("u", "p")
        client.send_message.assert_called_once()

    def test_no_tls(self) -> None:
        n = EmailNotifier("h", 25, "", "", "x@y.com", use_tls=False)
        u = [_proc("1", 1, date(2025, 5, 5))]
        client = _mk_client()
        with patch("smtplib.SMTP", return_value=client):
            n.notify_urgentes(u, to="adv@firma.com")
        client.starttls.assert_not_called()
        client.login.assert_not_called()

    def test_smtp_error_raises(self) -> None:
        n = _notifier()
        u = [_proc("1", 1, date(2025, 5, 5))]
        with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("boom")):
            with pytest.raises(EmailNotifierError):
                n.notify_urgentes(u, to="adv@firma.com")

    def test_oserror_raises(self) -> None:
        n = _notifier()
        u = [_proc("1", 1, date(2025, 5, 5))]
        with patch("smtplib.SMTP", side_effect=OSError("conn refused")):
            with pytest.raises(EmailNotifierError):
                n.notify_urgentes(u, to="adv@firma.com")

    def test_subject_includes_count_and_date(self) -> None:
        n = _notifier()
        u = [
            _proc("A", 1, date(2025, 5, 5)),
            _proc("B", 2, date(2025, 5, 5)),
        ]
        client = _mk_client()
        captured: dict[str, object] = {}

        def _capture_send(msg: object) -> None:
            captured["subject"] = msg["Subject"]  # type: ignore[index]
            captured["body"] = msg.get_content()  # type: ignore[attr-defined]

        client.send_message.side_effect = _capture_send
        with patch("smtplib.SMTP", return_value=client):
            n.notify_urgentes(u, to="adv@firma.com", hoje=date(2025, 5, 5))
        assert "2 prazo" in str(captured["subject"])
        assert "2025-05-05" in str(captured["subject"])

    def test_body_has_no_pii(self) -> None:
        n = _notifier()
        u = [_proc("0001234-56.2024.8.16.0001", 1, date(2025, 5, 5))]
        client = _mk_client()
        captured: dict[str, str] = {}

        def _capture(msg: object) -> None:
            captured["body"] = msg.get_content()  # type: ignore[attr-defined]

        client.send_message.side_effect = _capture
        with patch("smtplib.SMTP", return_value=client):
            n.notify_urgentes(u, to="adv@firma.com", hoje=date(2025, 5, 5))
        body = captured["body"]
        assert "0001234-56.2024.8.16.0001" in body
        # nada que pareca CPF/OAB
        assert "CPF" not in body
        assert "@" not in body.replace("nao", "")  # no email-like

    def test_custom_subject_prefix(self) -> None:
        n = _notifier()
        u = [_proc("1", 1, date(2025, 5, 5))]
        client = _mk_client()
        captured: dict[str, str] = {}
        client.send_message.side_effect = lambda msg: captured.update(
            {"s": msg["Subject"]}  # type: ignore[index]
        )
        with patch("smtplib.SMTP", return_value=client):
            n.notify_urgentes(u, to="x@y.com", subject_prefix="[CUSTOM]")
        assert captured["s"].startswith("[CUSTOM]")

    def test_skips_none_prazo(self) -> None:
        n = _notifier()
        parsed = Intimacao(
            numero_processo="X",
            data_publicacao=date(2025, 5, 5),
            prazo_dias=1,
            tipo_ato="ato",
        )
        u = [
            ProcessedIntimacao(
                numero_processo="X",
                redacted_text="",
                pii_matches=0,
                parsed=parsed,
                prazo=None,
            )
        ]
        client = _mk_client()
        captured: dict[str, str] = {}
        client.send_message.side_effect = lambda msg: captured.update(
            {"b": msg.get_content()}  # type: ignore[attr-defined]
        )
        with patch("smtplib.SMTP", return_value=client):
            count = n.notify_urgentes(u, to="x@y.com")
        # ainda conta no len, mas linha pulada
        assert count == 1
        assert "1. Processo" not in captured["b"]
