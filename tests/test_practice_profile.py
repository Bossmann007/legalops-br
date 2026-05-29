"""Tests para practice_profile — sem PII real."""

from __future__ import annotations

import re

import pytest

from legalops.practice_profile import (
    DEFAULT_PROFILE,
    AreaPratica,
    PracticeProfile,
    TeseRecorrente,
    get_teses_by_area,
    profile_summary,
)


class TestDefaultProfile:
    def test_escritorio_e_placeholder(self) -> None:
        assert DEFAULT_PROFILE.escritorio == "[ESCRITORIO]"

    def test_advogada_e_placeholder(self) -> None:
        assert DEFAULT_PROFILE.advogada_responsavel.startswith("[")
        assert DEFAULT_PROFILE.advogada_responsavel.endswith("]")

    def test_minimum_teses(self) -> None:
        assert len(DEFAULT_PROFILE.teses_recorrentes) >= 4

    def test_cidade_estado(self) -> None:
        assert DEFAULT_PROFILE.cidade == "Curitiba"
        assert DEFAULT_PROFILE.estado == "PR"

    def test_tem_tribunais(self) -> None:
        assert "TJPR" in DEFAULT_PROFILE.tribunais_principais


class TestGetTesesByArea:
    def test_bancario_tem_pelo_menos_2(self) -> None:
        teses = get_teses_by_area(DEFAULT_PROFILE, AreaPratica.BANCARIO)
        assert len(teses) >= 2

    def test_trabalhista_vazio(self) -> None:
        teses = get_teses_by_area(DEFAULT_PROFILE, AreaPratica.TRABALHISTA)
        assert teses == ()

    def test_lgpd_tem_tese(self) -> None:
        teses = get_teses_by_area(DEFAULT_PROFILE, AreaPratica.LGPD)
        assert len(teses) >= 1
        assert any("LGPD" in t.titulo for t in teses)


class TestProfileSummary:
    def test_returns_markdown_h1(self) -> None:
        out = profile_summary(DEFAULT_PROFILE)
        assert out.startswith("# Profile")

    def test_tem_secoes(self) -> None:
        out = profile_summary(DEFAULT_PROFILE)
        assert "## Teses Recorrentes" in out
        assert "## Politica de Honorarios" in out
        assert "## Politica IA" in out

    def test_no_cpf_pattern(self) -> None:
        out = profile_summary(DEFAULT_PROFILE)
        assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", out)

    def test_no_oab_real(self) -> None:
        out = profile_summary(DEFAULT_PROFILE)
        assert "[OAB_REDACTED]" in out


class TestImutability:
    def test_profile_is_frozen(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            DEFAULT_PROFILE.escritorio = "outro"  # type: ignore[misc]

    def test_tese_is_frozen(self) -> None:
        t = DEFAULT_PROFILE.teses_recorrentes[0]
        with pytest.raises(Exception):  # noqa: B017
            t.titulo = "outro"  # type: ignore[misc]


class TestFundamentos:
    def test_todas_teses_tem_fundamentos(self) -> None:
        for t in DEFAULT_PROFILE.teses_recorrentes:
            assert len(t.fundamentos) > 0
            assert all(isinstance(f, str) and f for f in t.fundamentos)


class TestEnum:
    def test_area_pratica_tem_8(self) -> None:
        assert len(list(AreaPratica)) == 8

    def test_bancario_e_str(self) -> None:
        assert AreaPratica.BANCARIO == "bancario"


class TestPracticeProfileType:
    def test_class_exists(self) -> None:
        assert PracticeProfile.__name__ == "PracticeProfile"

    def test_tese_class_exists(self) -> None:
        assert TeseRecorrente.__name__ == "TeseRecorrente"
