"""Tests para due_diligence — checklist sintetico."""

from __future__ import annotations

from legalops.due_diligence import (
    DueDiligenceChecklist,
    ItemDD,
    checklist_padrao,
)


class TestChecklistPadrao:
    def test_tem_itens(self) -> None:
        assert len(checklist_padrao().itens) > 0

    def test_cobre_cinco_areas(self) -> None:
        areas = {item.area for item in checklist_padrao().itens}
        assert areas == {"trabalhista", "fiscal", "ambiental", "contratual", "societario"}

    def test_todos_pendentes_inicialmente(self) -> None:
        assert all(item.status == "pendente" for item in checklist_padrao().itens)


class TestSetStatus:
    def test_atualiza_item_existente(self) -> None:
        chk = checklist_padrao()
        ok = chk.set_status("fiscal", "Certidao de tributos federais", "ok")
        assert ok is True

    def test_item_inexistente_retorna_false(self) -> None:
        chk = checklist_padrao()
        assert chk.set_status("fiscal", "item que nao existe", "ok") is False

    def test_status_persiste(self) -> None:
        chk = checklist_padrao()
        chk.set_status("fiscal", "Certidao de tributos federais", "critico")
        item = next(i for i in chk.itens if i.descricao == "Certidao de tributos federais")
        assert item.status == "critico"


class TestGaps:
    def test_pendentes_obrigatorios_sao_gaps(self) -> None:
        chk = checklist_padrao()
        gaps = chk.gaps()
        assert all(g.obrigatorio and g.status == "pendente" for g in gaps)

    def test_item_ok_nao_e_gap(self) -> None:
        chk = checklist_padrao()
        chk.set_status("fiscal", "Certidao de tributos federais", "ok")
        gaps = chk.gaps()
        assert not any(g.descricao == "Certidao de tributos federais" for g in gaps)

    def test_critico_e_gap(self) -> None:
        chk = DueDiligenceChecklist([ItemDD("fiscal", "x", True, "ref", "critico")])
        assert len(chk.gaps()) == 1

    def test_nao_obrigatorio_pendente_nao_e_gap(self) -> None:
        chk = DueDiligenceChecklist([ItemDD("fiscal", "x", False, "ref", "pendente")])
        assert chk.gaps() == ()


class TestScore:
    def test_tudo_ok_score_1(self) -> None:
        chk = DueDiligenceChecklist(
            [ItemDD("fiscal", "a", True, "r", "ok"), ItemDD("fiscal", "b", True, "r", "ok")]
        )
        assert chk.score() == 1.0

    def test_metade_ok(self) -> None:
        chk = DueDiligenceChecklist(
            [ItemDD("fiscal", "a", True, "r", "ok"), ItemDD("fiscal", "b", True, "r", "pendente")]
        )
        assert chk.score() == 0.5

    def test_nao_aplicavel_sai_do_denominador(self) -> None:
        chk = DueDiligenceChecklist(
            [
                ItemDD("fiscal", "a", True, "r", "ok"),
                ItemDD("fiscal", "b", True, "r", "nao_aplicavel"),
            ]
        )
        assert chk.score() == 1.0

    def test_sem_aplicaveis_score_1(self) -> None:
        chk = DueDiligenceChecklist([ItemDD("fiscal", "a", False, "r", "pendente")])
        assert chk.score() == 1.0


class TestResumoPorArea:
    def test_conta_por_status(self) -> None:
        chk = DueDiligenceChecklist(
            [
                ItemDD("fiscal", "a", True, "r", "ok"),
                ItemDD("fiscal", "b", True, "r", "pendente"),
            ]
        )
        resumo = chk.resumo_por_area()
        assert resumo["fiscal"] == {"ok": 1, "pendente": 1}

    def test_areas_distintas(self) -> None:
        chk = DueDiligenceChecklist(
            [ItemDD("fiscal", "a", True, "r", "ok"), ItemDD("trabalhista", "b", True, "r", "ok")]
        )
        assert set(chk.resumo_por_area().keys()) == {"fiscal", "trabalhista"}
