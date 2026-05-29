"""Tests for dsar module (Art. 18/19 LGPD)."""

from __future__ import annotations

from datetime import date

import pytest

from legalops.dsar import (
    DSARError,
    DSARRequest,
    classify_request,
    processar_dsar,
)


class TestClassifyRequest:
    def test_acesso(self) -> None:
        assert classify_request("quero acessar meus dados") == "acesso"

    def test_eliminacao(self) -> None:
        assert classify_request("apague todos os meus dados") == "eliminacao"

    def test_correcao(self) -> None:
        assert classify_request("preciso corrigir meu cadastro") == "correcao"

    def test_portabilidade(self) -> None:
        assert classify_request("quero portar meus dados a outro fornecedor") == "portabilidade"

    def test_revogacao_consentimento(self) -> None:
        assert classify_request("desejo revogar meu consentimento") == "revogacao_consentimento"

    def test_confirmacao(self) -> None:
        assert classify_request("quero confirmar se tratam meus dados") == "confirmacao"

    def test_oposicao(self) -> None:
        assert classify_request("me oponho a esse tratamento") == "oposicao"

    def test_anonimizacao(self) -> None:
        assert classify_request("quero anonimizar meus dados") == "anonimizacao"

    def test_compartilhamento(self) -> None:
        assert classify_request("com quem voces compartilham?") == "informacao_compartilhamento"

    def test_unclassifiable_returns_empty(self) -> None:
        assert classify_request("ola, bom dia") == ""

    def test_empty_returns_empty(self) -> None:
        assert classify_request("") == ""


class TestProcessarDSAR:
    def test_prazo_final_recebimento_mais_15(self) -> None:
        req = DSARRequest("r1", "acesso", date(2026, 1, 1), "titular-abc")

        resp = processar_dsar(req, hoje=date(2026, 1, 1))

        assert resp.prazo_final == date(2026, 1, 16)

    def test_status_no_prazo(self) -> None:
        req = DSARRequest("r1", "acesso", date(2026, 1, 1), "titular-abc")

        resp = processar_dsar(req, hoje=date(2026, 1, 10))

        assert resp.status == "no_prazo"

    def test_status_vence_hoje(self) -> None:
        req = DSARRequest("r1", "acesso", date(2026, 1, 1), "titular-abc")

        resp = processar_dsar(req, hoje=date(2026, 1, 16))

        assert resp.status == "vence_hoje"

    def test_status_em_atraso(self) -> None:
        req = DSARRequest("r1", "acesso", date(2026, 1, 1), "titular-abc")

        resp = processar_dsar(req, hoje=date(2026, 2, 1))

        assert resp.status == "em_atraso"

    def test_dias_restantes_calculado(self) -> None:
        req = DSARRequest("r1", "acesso", date(2026, 1, 1), "titular-abc")

        resp = processar_dsar(req, hoje=date(2026, 1, 5))

        assert resp.dias_restantes == 11

    def test_artigo_preenchido(self) -> None:
        req = DSARRequest("r1", "acesso", date(2026, 1, 1), "titular-abc")

        resp = processar_dsar(req, hoje=date(2026, 1, 1))

        assert resp.artigo == "Art. 18 II"

    def test_texto_cita_descricao(self) -> None:
        req = DSARRequest("r1", "eliminacao", date(2026, 1, 1), "titular-abc")

        resp = processar_dsar(req, hoje=date(2026, 1, 1))

        assert "Art. 19" in resp.texto_resposta

    def test_codigo_invalido_raises(self) -> None:
        req = DSARRequest("r1", "inexistente", date(2026, 1, 1), "titular-abc")

        with pytest.raises(DSARError):
            processar_dsar(req, hoje=date(2026, 1, 1))

    def test_hoje_none_usa_today(self) -> None:
        req = DSARRequest("r1", "acesso", date.today(), "titular-abc")

        resp = processar_dsar(req)

        assert resp.dias_restantes == 15
