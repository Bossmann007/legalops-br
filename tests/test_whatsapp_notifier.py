"""Tests para whatsapp_notifier — sem chamada real ao bridge."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from legalops.cpc_prazos import PrazoInput, calcular_prazo
from legalops.orchestrator import ProcessedIntimacao
from legalops.tjpr_parser import Intimacao
from legalops.whatsapp_notifier import (
    DEFAULT_BRIDGE_URL,
    WhatsAppNotifier,
    WhatsAppNotifierError,
)


FAKE_CHAT_ID = "5541999999999@s.whatsapp.net"


def _fake_intimacao(numero: str, prazo_dias: int, hoje: date) -> ProcessedIntimacao:
    """Cria ProcessedIntimacao sintetica via calculo real."""
    parsed = Intimacao(
        numero_processo=numero,
        data_publicacao=hoje,
        prazo_dias=prazo_dias,
        tipo_ato="despacho",
    )
    prazo = calcular_prazo(
        PrazoInput(
            data_publicacao=hoje, prazo_dias=prazo_dias, parte="particular"
        ),
        hoje=hoje,
    )
    return ProcessedIntimacao(
        numero_processo=numero,
        redacted_text="",
        pii_matches=0,
        parsed=parsed,
        prazo=prazo,
    )


def _mock_resp(status: int = 200, body: bytes = b'{"ok": true}') -> MagicMock:
    m = MagicMock()
    m.status = status
    m.read.return_value = body
    m.__enter__ = lambda self: self
    m.__exit__ = lambda *a: None
    return m


class TestInit:
    def test_default_url(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        assert n.base_url == DEFAULT_BRIDGE_URL
        assert n.chat_id == FAKE_CHAT_ID

    def test_custom_url_strip_slash(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID, base_url="http://example/")
        assert n.base_url == "http://example"

    def test_empty_chat_id_raises(self) -> None:
        with pytest.raises(ValueError, match="chat_id"):
            WhatsAppNotifier(chat_id="")

    def test_invalid_scheme_ftp_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme invalido"):
            WhatsAppNotifier(chat_id=FAKE_CHAT_ID, base_url="ftp://example.com")

    def test_invalid_scheme_file_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme invalido"):
            WhatsAppNotifier(chat_id=FAKE_CHAT_ID, base_url="file:///etc/passwd")

    def test_no_host_raises(self) -> None:
        with pytest.raises(ValueError, match="sem host"):
            WhatsAppNotifier(chat_id=FAKE_CHAT_ID, base_url="http://")

    def test_https_accepted(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID, base_url="https://bridge.example/")
        assert n.base_url == "https://bridge.example"


class TestSend:
    def test_send_post_payload(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        with patch(
            "legalops.whatsapp_notifier.request.urlopen",
            return_value=_mock_resp(200, b'{"ok": true, "id": "abc"}'),
        ) as mock_open:
            result = n.send("teste")
        assert result == {"ok": True, "id": "abc"}
        called_req = mock_open.call_args[0][0]
        assert called_req.full_url.endswith("/send")
        body = json.loads(called_req.data.decode())
        assert body["chatId"] == FAKE_CHAT_ID
        assert body["message"] == "teste"

    def test_send_empty_message_raises(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        with pytest.raises(ValueError, match="vazia"):
            n.send("")

    def test_send_http_error_raises(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        with patch(
            "legalops.whatsapp_notifier.request.urlopen",
            return_value=_mock_resp(500, b"server error"),
        ):
            with pytest.raises(WhatsAppNotifierError, match="HTTP 500"):
                n.send("teste")

    def test_send_bridge_offline_raises(self) -> None:
        from urllib.error import URLError

        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID, timeout=0.1)
        with patch(
            "legalops.whatsapp_notifier.request.urlopen",
            side_effect=URLError("connection refused"),
        ):
            with pytest.raises(WhatsAppNotifierError, match="unreachable"):
                n.send("teste")

    def test_send_empty_body_returns_empty_dict(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        with patch(
            "legalops.whatsapp_notifier.request.urlopen",
            return_value=_mock_resp(200, b""),
        ):
            result = n.send("teste")
        assert result == {}


class TestFormatUrgentesMessage:
    def test_one_urgente(self) -> None:
        hoje = date(2026, 5, 22)
        intim = _fake_intimacao("0001234-56.2026.8.16.0001", 3, hoje)
        msg = WhatsAppNotifier.format_urgentes_message([intim], hoje=hoje)
        assert "PRAZOS URGENTES" in msg
        assert "0001234-56.2026.8.16.0001" in msg
        assert "2026-05-22" in msg
        assert "1 prazo" in msg

    def test_no_cpf_pattern_in_msg(self) -> None:
        import re

        hoje = date(2026, 5, 22)
        intim = _fake_intimacao("0001234-56.2026.8.16.0001", 2, hoje)
        msg = WhatsAppNotifier.format_urgentes_message([intim], hoje=hoje)
        assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", msg)

    def test_multiple_urgentes(self) -> None:
        hoje = date(2026, 5, 22)
        items = [
            _fake_intimacao("0001111-11.2026.8.16.0001", 2, hoje),
            _fake_intimacao("0002222-22.2026.8.16.0002", 3, hoje),
        ]
        msg = WhatsAppNotifier.format_urgentes_message(items, hoje=hoje)
        assert "2 prazo" in msg
        assert "0001111-11" in msg
        assert "0002222-22" in msg


class TestNotifyUrgentes:
    def test_no_urgentes_returns_none_no_send(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        hoje = date(2026, 5, 22)
        intim = _fake_intimacao("0001111-11.2026.8.16.0001", 30, hoje)
        with patch("legalops.whatsapp_notifier.request.urlopen") as mock_open:
            result = n.notify_urgentes([intim], hoje=hoje)
        assert result is None
        mock_open.assert_not_called()

    def test_urgente_envia(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        hoje = date(2026, 5, 22)
        intim = _fake_intimacao("0001111-11.2026.8.16.0001", 2, hoje)
        with patch(
            "legalops.whatsapp_notifier.request.urlopen", return_value=_mock_resp()
        ) as mock_open:
            msg = n.notify_urgentes([intim], hoje=hoje)
        assert msg is not None
        assert "0001111-11" in msg
        assert mock_open.called

    def test_filter_alerta_atencao_nao_envia(self) -> None:
        n = WhatsAppNotifier(chat_id=FAKE_CHAT_ID)
        hoje = date(2026, 5, 22)
        # 7 dias = ATENCAO, nao URGENTE
        intim = _fake_intimacao("0001111-11.2026.8.16.0001", 7, hoje)
        with patch("legalops.whatsapp_notifier.request.urlopen") as mock_open:
            result = n.notify_urgentes([intim], hoje=hoje)
        assert result is None
        mock_open.assert_not_called()
