"""Tests M365 ingest — mock urllib.request.urlopen para validar auth + fetch."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from legalops.m365_ingest import (
    M365Client,
    M365Email,
    M365Error,
    _strip_html,
    integrate_with_pipeline,
)


def _mock_response(payload: dict[str, Any], status: int = 200) -> MagicMock:
    """Build a MagicMock that behaves like urlopen's context-manager response."""
    raw = json.dumps(payload).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = raw
    cm.__enter__.return_value.status = status
    cm.__exit__.return_value = False
    return cm


def _http_error(status: int, body: str) -> HTTPError:
    return HTTPError(
        url="https://example.test",
        code=status,
        msg="err",
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(body.encode("utf-8")),
    )


class TestM365Email:
    def test_dataclass_shape(self) -> None:
        em = M365Email(
            message_id="abc",
            subject="Intimacao",
            sender="x@tjsp.jus.br",
            received_at=datetime(2026, 5, 28, tzinfo=UTC),
            body_text="content",
            has_attachments=False,
        )
        assert em.subject == "Intimacao"
        assert em.message_id == "abc"


class TestStripHtml:
    def test_basic(self) -> None:
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_script_removed(self) -> None:
        html = "<p>keep</p><script>alert('x')</script><p>this</p>"
        assert "alert" not in _strip_html(html)


class TestInit:
    def test_init_state(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        assert c.tenant_id == "t"
        assert c.client_id == "c"
        assert c._token is None
        assert c._token_expires_at is None


class TestAuthenticate:
    def test_authenticate_posts_correct_form(self) -> None:
        c = M365Client(
            tenant_id="tenant-x",
            client_id="cid",
            client_secret="sec",  # noqa: S106
        )
        resp = _mock_response({"access_token": "TKN", "expires_in": 3600})

        with patch("urllib.request.urlopen", return_value=resp) as mock_open:
            token = c._authenticate()

        assert token == "TKN"  # noqa: S105
        req = mock_open.call_args[0][0]
        # URL contains tenant
        assert "tenant-x" in req.full_url
        assert req.method == "POST"
        # Form-encoded body has required fields
        body = req.data.decode("utf-8")
        assert "client_id=cid" in body
        assert "client_secret=sec" in body
        assert "grant_type=client_credentials" in body
        assert "scope=https" in body
        assert ".default" in body

    def test_authenticate_caches_token(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        resp = _mock_response({"access_token": "T1", "expires_in": 3600})

        with patch("urllib.request.urlopen", return_value=resp) as mock_open:
            t1 = c._authenticate()
            t2 = c._authenticate()

        assert t1 == "T1"
        assert t2 == "T1"
        assert mock_open.call_count == 1

    def test_authenticate_reauths_when_expired(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        c._token = "OLD"  # noqa: S105
        c._token_expires_at = datetime.now(UTC) - timedelta(seconds=10)
        resp = _mock_response({"access_token": "NEW", "expires_in": 3600})

        with patch("urllib.request.urlopen", return_value=resp):
            tok = c._authenticate()

        assert tok == "NEW"

    def test_authenticate_http_error_raises(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106

        with patch(
            "urllib.request.urlopen",
            side_effect=_http_error(401, '{"error":"invalid_client"}'),
        ):
            with pytest.raises(M365Error, match="HTTP 401"):
                c._authenticate()

    def test_authenticate_network_error_raises(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        with patch("urllib.request.urlopen", side_effect=URLError("no DNS")):
            with pytest.raises(M365Error, match="Network error"):
                c._authenticate()

    def test_authenticate_missing_token_raises(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        resp = _mock_response({"expires_in": 3600})  # no access_token
        with patch("urllib.request.urlopen", return_value=resp):
            with pytest.raises(M365Error, match="access_token"):
                c._authenticate()


class TestFetchRecent:
    def _client_authed(self) -> M365Client:
        c = M365Client(
            tenant_id="t",
            client_id="c",
            client_secret="s",  # noqa: S106
            user_principal_name="adv@firma.com.br",
        )
        c._token = "TKN"  # noqa: S105
        c._token_expires_at = datetime.now(UTC) + timedelta(hours=1)
        return c

    def test_fetch_recent_builds_correct_url(self) -> None:
        c = self._client_authed()
        graph_payload = {
            "value": [
                {
                    "id": "msg-1",
                    "subject": "Intimacao TJSP",
                    "from": {"emailAddress": {"address": "noreply@tjsp.jus.br"}},
                    "receivedDateTime": "2026-05-28T10:00:00Z",
                    "body": {"contentType": "text", "content": "Conteudo do email"},
                    "hasAttachments": False,
                }
            ]
        }
        resp = _mock_response(graph_payload)

        with patch("urllib.request.urlopen", return_value=resp) as mock_open:
            emails = c.fetch_recent(
                folder="Inbox",
                days=7,
                sender_filter="noreply@tjsp.jus.br",
                max_results=50,
            )

        assert len(emails) == 1
        em = emails[0]
        assert em.message_id == "msg-1"
        assert em.sender == "noreply@tjsp.jus.br"
        assert em.body_text == "Conteudo do email"

        req = mock_open.call_args[0][0]
        url = req.full_url
        assert "/users/adv@firma.com.br/mailFolders/Inbox/messages" in url
        assert "%24top=50" in url
        assert "receivedDateTime+ge" in url or "receivedDateTime%20ge" in url
        assert "Bearer TKN" in req.headers.get("Authorization", "")

    def test_fetch_recent_strips_html(self) -> None:
        c = self._client_authed()
        graph_payload = {
            "value": [
                {
                    "id": "msg-html",
                    "subject": "S",
                    "from": {"emailAddress": {"address": "x@y.com"}},
                    "receivedDateTime": "2026-05-28T10:00:00Z",
                    "body": {
                        "contentType": "html",
                        "content": "<p>Hello <b>world</b></p>",
                    },
                    "hasAttachments": True,
                }
            ]
        }
        resp = _mock_response(graph_payload)
        with patch("urllib.request.urlopen", return_value=resp):
            emails = c.fetch_recent()
        assert emails[0].body_text == "Hello world"
        assert emails[0].has_attachments is True

    def test_fetch_recent_pagination(self) -> None:
        c = self._client_authed()
        page1 = {
            "value": [
                {
                    "id": f"m{i}",
                    "subject": "s",
                    "from": {"emailAddress": {"address": "a@b.com"}},
                    "receivedDateTime": "2026-05-28T10:00:00Z",
                    "body": {"contentType": "text", "content": "x"},
                    "hasAttachments": False,
                }
                for i in range(2)
            ],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/page2",
        }
        page2 = {
            "value": [
                {
                    "id": "m2",
                    "subject": "s",
                    "from": {"emailAddress": {"address": "a@b.com"}},
                    "receivedDateTime": "2026-05-28T10:00:00Z",
                    "body": {"contentType": "text", "content": "y"},
                    "hasAttachments": False,
                }
            ]
        }
        responses = [_mock_response(page1), _mock_response(page2)]
        with patch("urllib.request.urlopen", side_effect=responses):
            emails = c.fetch_recent(max_results=100)
        assert len(emails) == 3
        assert [e.message_id for e in emails] == ["m0", "m1", "m2"]

    def test_fetch_recent_respects_max_results(self) -> None:
        c = self._client_authed()
        page = {
            "value": [
                {
                    "id": f"m{i}",
                    "subject": "s",
                    "from": {"emailAddress": {"address": "a@b.com"}},
                    "receivedDateTime": "2026-05-28T10:00:00Z",
                    "body": {"contentType": "text", "content": "x"},
                    "hasAttachments": False,
                }
                for i in range(5)
            ],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/page2",
        }
        with patch("urllib.request.urlopen", return_value=_mock_response(page)):
            emails = c.fetch_recent(max_results=3)
        assert len(emails) == 3

    def test_fetch_recent_requires_upn(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        with pytest.raises(M365Error, match="user_principal_name"):
            c.fetch_recent()

    def test_fetch_recent_http_error(self) -> None:
        c = self._client_authed()
        with patch(
            "urllib.request.urlopen",
            side_effect=_http_error(403, '{"error":"forbidden"}'),
        ):
            with pytest.raises(M365Error, match="HTTP 403"):
                c.fetch_recent()


class TestFetchById:
    def test_fetch_by_id_ok(self) -> None:
        c = M365Client(
            tenant_id="t",
            client_id="c",
            client_secret="s",  # noqa: S106
            user_principal_name="u@x.com",
        )
        c._token = "TKN"  # noqa: S105
        c._token_expires_at = datetime.now(UTC) + timedelta(hours=1)
        payload = {
            "id": "abc-1",
            "subject": "Hi",
            "from": {"emailAddress": {"address": "s@x.com"}},
            "receivedDateTime": "2026-05-28T10:00:00Z",
            "body": {"contentType": "text", "content": "body"},
            "hasAttachments": False,
        }
        with patch("urllib.request.urlopen", return_value=_mock_response(payload)) as mock_open:
            em = c.fetch_by_id("abc-1")
        assert em.message_id == "abc-1"
        url = mock_open.call_args[0][0].full_url
        assert "/users/u@x.com/messages/abc-1" in url


class TestIntegration:
    def test_integrate_with_pipeline_empty(self) -> None:
        assert integrate_with_pipeline([]) == []

    def test_integrate_with_pipeline_calls_process(self) -> None:
        em = M365Email(
            message_id="m1",
            subject="s",
            sender="noreply@tjsp.jus.br",
            received_at=datetime(2026, 5, 28, tzinfo=UTC),
            body_text="texto sem processo CNJ",
            has_attachments=False,
        )
        # Should not raise even if nothing parses
        out = integrate_with_pipeline([em])
        assert out == []

    def test_integrate_with_pipeline_swallows_errors(self) -> None:
        em = M365Email(
            message_id="m1",
            subject="s",
            sender="x@y.com",
            received_at=datetime(2026, 5, 28, tzinfo=UTC),
            body_text="",
            has_attachments=False,
        )
        with patch("legalops.orchestrator.process_email", side_effect=RuntimeError("boom")):
            out = integrate_with_pipeline([em])
        assert out == []
