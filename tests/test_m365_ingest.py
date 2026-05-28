"""Tests stub M365 — verifica interface + raise NotImplementedError."""

from __future__ import annotations

import pytest

from legalops.m365_ingest import M365Client, M365Email, integrate_with_pipeline


class TestM365Client:
    def test_init_no_call(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        assert c.tenant_id == "t"
        assert c.client_id == "c"
        assert c._token is None

    def test_fetch_recent_not_implemented(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        with pytest.raises(NotImplementedError):
            c.fetch_recent()

    def test_authenticate_not_implemented(self) -> None:
        c = M365Client(tenant_id="t", client_id="c", client_secret="s")  # noqa: S106
        with pytest.raises(NotImplementedError):
            c._authenticate()


class TestM365Email:
    def test_dataclass_shape(self) -> None:
        from datetime import datetime

        em = M365Email(
            message_id="abc",
            subject="Intimacao",
            sender="x@tjsp.jus.br",
            received_at=datetime(2026, 5, 28),
            body_text="content",
            has_attachments=False,
        )
        assert em.subject == "Intimacao"


class TestIntegration:
    def test_helper_stub_raises(self) -> None:
        with pytest.raises(NotImplementedError):
            integrate_with_pipeline([])
