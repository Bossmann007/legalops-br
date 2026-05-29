"""Tests para disclosure — representacoes e schedule sinteticos."""

from __future__ import annotations

from legalops.disclosure import (
    DisclosureItem,
    DisclosureSchedule,
    Representacao,
    find_gaps,
    inconsistencias,
)


class TestFindGaps:
    def test_gap_quando_requer_e_sem_item(self) -> None:
        reps = (Representacao("R-1", "texto", True),)
        gaps = find_gaps(reps, DisclosureSchedule())
        assert gaps == reps

    def test_sem_gap_quando_coberto(self) -> None:
        reps = (Representacao("R-1", "texto", True),)
        sched = DisclosureSchedule([DisclosureItem("R-1", "divulgacao")])
        assert find_gaps(reps, sched) == ()

    def test_rep_que_nao_requer_nunca_e_gap(self) -> None:
        reps = (Representacao("R-2", "texto", False),)
        assert find_gaps(reps, DisclosureSchedule()) == ()

    def test_reps_vazias(self) -> None:
        assert find_gaps((), DisclosureSchedule()) == ()


class TestInconsistencias:
    def test_item_orfao(self) -> None:
        reps = (Representacao("R-1", "texto", True),)
        sched = DisclosureSchedule([DisclosureItem("R-9", "orfao")])
        result = inconsistencias(reps, sched)
        assert result[0].rep_id == "R-9"

    def test_sem_inconsistencia(self) -> None:
        reps = (Representacao("R-1", "texto", True),)
        sched = DisclosureSchedule([DisclosureItem("R-1", "divulgacao")])
        assert inconsistencias(reps, sched) == ()

    def test_schedule_vazio(self) -> None:
        reps = (Representacao("R-1", "texto", True),)
        assert inconsistencias(reps, DisclosureSchedule()) == ()


class TestDisclosureSchedule:
    def test_add_e_items(self) -> None:
        sched = DisclosureSchedule()
        sched.add(DisclosureItem("R-1", "x"))
        assert len(sched.items) == 1

    def test_rep_ids(self) -> None:
        sched = DisclosureSchedule([DisclosureItem("R-1", "x"), DisclosureItem("R-2", "y")])
        assert sched.rep_ids() == frozenset({"R-1", "R-2"})
