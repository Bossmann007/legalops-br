"""Tests para vendor_ai_review — checklist de fornecedor de IA (sintetico)."""

from __future__ import annotations

import pytest

from legalops.vendor_ai_review import (
    ItemVendorReview,
    VendorReview,
    checklist_vendor_padrao,
)


class TestChecklistPadrao:
    def test_tem_itens(self) -> None:
        assert len(checklist_vendor_padrao().itens) > 0

    def test_todos_pendentes_inicialmente(self) -> None:
        assert all(item.status == "pendente" for item in checklist_vendor_padrao().itens)

    def test_cobre_transferencia_internacional(self) -> None:
        chaves = {item.chave for item in checklist_vendor_padrao().itens}
        assert "transferencia_internacional" in chaves

    def test_zdr_e_opcional(self) -> None:
        item = next(i for i in checklist_vendor_padrao().itens if i.chave == "zero_data_retention")
        assert item.obrigatorio is False


class TestSetStatus:
    def test_atualiza_item_existente(self) -> None:
        rev = checklist_vendor_padrao()
        assert rev.set_status("operador_dpa", "ok") is True

    def test_item_inexistente_retorna_false(self) -> None:
        rev = checklist_vendor_padrao()
        assert rev.set_status("inexistente", "ok") is False

    @pytest.mark.parametrize(
        "status",
        ["pendente", "ok", "alerta", "critico", "nao_aplicavel"],
    )
    def test_aceita_cada_status(self, status: str) -> None:
        rev = checklist_vendor_padrao()
        rev.set_status("seguranca_criptografia", status)  # type: ignore[arg-type]
        item = next(i for i in rev.itens if i.chave == "seguranca_criptografia")
        assert item.status == status


class TestFlags:
    def test_pendente_obrigatorio_e_flag(self) -> None:
        rev = checklist_vendor_padrao()
        assert len(rev.flags()) > 0

    def test_critico_e_flag(self) -> None:
        rev = VendorReview([ItemVendorReview("x", "p?", "Art. 46", status="critico")])
        assert rev.flags()[0].chave == "x"

    def test_ok_nao_e_flag(self) -> None:
        rev = VendorReview([ItemVendorReview("x", "p?", "Art. 46", status="ok")])
        assert rev.flags() == ()

    def test_opcional_pendente_nao_e_flag(self) -> None:
        rev = VendorReview([ItemVendorReview("x", "p?", "Art. 16", obrigatorio=False)])
        assert rev.flags() == ()


class TestScore:
    def test_todos_ok_score_um(self) -> None:
        rev = checklist_vendor_padrao()
        for item in rev.itens:
            rev.set_status(item.chave, "ok")
        assert rev.score() == 1.0

    def test_metade_ok(self) -> None:
        rev = VendorReview(
            [
                ItemVendorReview("a", "?", "Art. 46", status="ok"),
                ItemVendorReview("b", "?", "Art. 33", status="pendente"),
            ]
        )
        assert rev.score() == 0.5

    def test_sem_aplicaveis_score_um(self) -> None:
        rev = VendorReview([ItemVendorReview("a", "?", "Art. 46", status="nao_aplicavel")])
        assert rev.score() == 1.0


class TestAprovado:
    def test_inicial_nao_aprovado(self) -> None:
        assert checklist_vendor_padrao().aprovado() is False

    def test_todos_ok_aprovado(self) -> None:
        rev = checklist_vendor_padrao()
        for item in rev.itens:
            rev.set_status(item.chave, "ok")
        assert rev.aprovado() is True

    def test_critico_reprova(self) -> None:
        rev = checklist_vendor_padrao()
        for item in rev.itens:
            rev.set_status(item.chave, "ok")
        rev.set_status("decisao_automatizada", "critico")
        assert rev.aprovado() is False

    def test_opcional_pendente_nao_reprova(self) -> None:
        rev = checklist_vendor_padrao()
        for item in rev.itens:
            if item.obrigatorio:
                rev.set_status(item.chave, "ok")
        assert rev.aprovado() is True
