"""Golden tests para cpc_prazos — datas hardcoded, deterministico."""

from __future__ import annotations

from datetime import date

import pytest

from legalops.cpc_prazos import (
    PrazoInput,
    _easter_date,
    calcular_prazo,
    conta_dias_uteis_entre,
    feriados_moveis,
    is_dia_util,
    is_feriado,
    is_recesso_forense_tjpr,
    proximo_dia_util,
    soma_dias_uteis,
)


class TestEaster:
    def test_easter_2026(self) -> None:
        assert _easter_date(2026) == date(2026, 4, 5)

    def test_easter_2027(self) -> None:
        assert _easter_date(2027) == date(2027, 3, 28)

    def test_easter_2024(self) -> None:
        assert _easter_date(2024) == date(2024, 3, 31)


class TestFeriadosMoveis:
    def test_carnaval_2026(self) -> None:
        feriados = feriados_moveis(2026)
        assert date(2026, 2, 16) in feriados
        assert date(2026, 2, 17) in feriados

    def test_sexta_paixao_2026(self) -> None:
        feriados = feriados_moveis(2026)
        assert date(2026, 4, 3) in feriados

    def test_corpus_christi_2026(self) -> None:
        feriados = feriados_moveis(2026)
        assert date(2026, 6, 4) in feriados


class TestRecessoForense:
    def test_dezembro_dentro(self) -> None:
        assert is_recesso_forense_tjpr(date(2026, 12, 25))
        assert is_recesso_forense_tjpr(date(2026, 12, 20))
        assert is_recesso_forense_tjpr(date(2026, 12, 31))

    def test_janeiro_dentro(self) -> None:
        assert is_recesso_forense_tjpr(date(2027, 1, 1))
        assert is_recesso_forense_tjpr(date(2027, 1, 20))

    def test_fora_recesso(self) -> None:
        assert not is_recesso_forense_tjpr(date(2026, 12, 19))
        assert not is_recesso_forense_tjpr(date(2027, 1, 21))
        assert not is_recesso_forense_tjpr(date(2026, 6, 15))


class TestFeriado:
    def test_natal(self) -> None:
        assert is_feriado(date(2026, 12, 25))

    def test_tiradentes(self) -> None:
        assert is_feriado(date(2026, 4, 21))

    def test_consciencia_negra(self) -> None:
        assert is_feriado(date(2026, 11, 20))

    def test_dia_comum(self) -> None:
        assert not is_feriado(date(2026, 6, 17))


class TestDiaUtil:
    def test_quarta_normal(self) -> None:
        assert is_dia_util(date(2026, 6, 17))

    def test_sabado(self) -> None:
        assert not is_dia_util(date(2026, 5, 23))

    def test_domingo(self) -> None:
        assert not is_dia_util(date(2026, 5, 24))

    def test_feriado(self) -> None:
        assert not is_dia_util(date(2026, 5, 1))


class TestProximoDiaUtil:
    def test_ja_e_dia_util(self) -> None:
        d = date(2026, 6, 17)
        assert proximo_dia_util(d) == d

    def test_pula_fim_de_semana(self) -> None:
        assert proximo_dia_util(date(2026, 5, 23)) == date(2026, 5, 25)

    def test_pula_feriado(self) -> None:
        assert proximo_dia_util(date(2026, 5, 1)) == date(2026, 5, 4)


class TestSomaDiasUteis:
    def test_zero_dias(self) -> None:
        assert soma_dias_uteis(date(2026, 6, 17), 0) == date(2026, 6, 17)

    def test_1_dia(self) -> None:
        assert soma_dias_uteis(date(2026, 6, 17), 1) == date(2026, 6, 18)

    def test_pula_weekend(self) -> None:
        assert soma_dias_uteis(date(2026, 6, 19), 1) == date(2026, 6, 22)


class TestContaDiasUteis:
    def test_mesma_data(self) -> None:
        assert conta_dias_uteis_entre(date(2026, 6, 17), date(2026, 6, 17)) == 0

    def test_proximo_util(self) -> None:
        assert conta_dias_uteis_entre(date(2026, 6, 17), date(2026, 6, 18)) == 1

    def test_atravessa_weekend(self) -> None:
        assert conta_dias_uteis_entre(date(2026, 6, 19), date(2026, 6, 23)) == 2


class TestCalcularPrazoBasico:
    def test_15_dias_uteis_particular(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 5, 21),
            prazo_dias=15,
            tipo_dia="uteis",
            parte="particular",
            via_dje=False,
        )
        result = calcular_prazo(inp, hoje=date(2026, 5, 22))
        assert result.data_intimacao_considerada == date(2026, 5, 21)
        assert result.dies_a_quo == date(2026, 5, 22)
        # Pula Corpus Christi 04/06/2026 -> ad_quem = 12/06
        assert result.dies_ad_quem == date(2026, 6, 12)
        assert result.prazo_efetivo_dias == 15

    def test_fazenda_dobro(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 5, 21),
            prazo_dias=15,
            tipo_dia="uteis",
            parte="fazenda",
            via_dje=False,
        )
        result = calcular_prazo(inp, hoje=date(2026, 5, 22))
        assert result.prazo_efetivo_dias == 30
        assert "Fazenda em dobro" in " ".join(result.fundamentos_aplicados)

    def test_fazenda_dje_sem_dobro(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 5, 21),
            prazo_dias=15,
            tipo_dia="uteis",
            parte="fazenda",
            via_dje=True,
        )
        result = calcular_prazo(inp)
        assert result.prazo_efetivo_dias == 15

    def test_mp_dobro(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 5, 21),
            prazo_dias=15,
            parte="mp",
        )
        result = calcular_prazo(inp)
        assert result.prazo_efetivo_dias == 30

    def test_defensoria_dobro(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 5, 21),
            prazo_dias=15,
            parte="defensoria",
        )
        result = calcular_prazo(inp)
        assert result.prazo_efetivo_dias == 30


class TestAlerta:
    def test_normal_amplo(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 5, 21),
            prazo_dias=30,
            parte="particular",
        )
        result = calcular_prazo(inp, hoje=date(2026, 5, 22))
        assert result.alerta == "NORMAL"


class TestRecessoForenseIntegracao:
    def test_prazo_atravessa_recesso(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 12, 10),
            prazo_dias=15,
            parte="particular",
        )
        result = calcular_prazo(inp, hoje=date(2026, 12, 11))
        assert result.dies_a_quo == date(2026, 12, 11)
        assert result.dies_ad_quem > date(2027, 1, 20)


class TestDJE:
    def test_intimacao_dje_pula_um_dia(self) -> None:
        inp = PrazoInput(
            data_publicacao=date(2026, 5, 21),
            prazo_dias=15,
            parte="particular",
            via_dje=True,
        )
        result = calcular_prazo(inp, hoje=date(2026, 5, 22))
        assert result.data_intimacao_considerada == date(2026, 5, 22)
        assert result.dies_a_quo == date(2026, 5, 25)


@pytest.mark.parametrize(
    "parte,esperado_dobro",
    [
        ("particular", False),
        ("fazenda", True),
        ("mp", True),
        ("defensoria", True),
    ],
)
def test_dobro_por_parte(parte: str, esperado_dobro: bool) -> None:
    inp = PrazoInput(
        data_publicacao=date(2026, 5, 21),
        prazo_dias=15,
        parte=parte,  # type: ignore[arg-type]
        via_dje=False,
    )
    result = calcular_prazo(inp)
    assert (result.prazo_efetivo_dias == 30) == esperado_dobro
