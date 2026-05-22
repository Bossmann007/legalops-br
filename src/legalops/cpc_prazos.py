"""Calculo deterministico de prazos processuais CPC/2015.

Implementa:
- Art. 219: prazos em dias uteis
- Art. 224: dies a quo = primeiro dia util seguinte a intimacao
- Art. 231 #1: intimacao eletronica = dia util seguinte ao envio
- Art. 183: Fazenda Publica prazo em dobro
- Art. 180: MP prazo em dobro
- Art. 186: Defensoria prazo em dobro

Feriados:
- Nacionais BR (Lei 662/49, Lei 6.802/80, Lei 14.759/2023)
- Recesso forense TJPR (20/12 a 20/01)
- Moveis: Carnaval, Quinta-feira Santa, Sexta-feira Santa, Corpus Christi

Uso:
    >>> from datetime import date
    >>> from legalops.cpc_prazos import PrazoInput, calcular_prazo
    >>> r = calcular_prazo(PrazoInput(
    ...     data_publicacao=date(2026, 5, 21),
    ...     prazo_dias=15,
    ...     tipo_dia="uteis",
    ...     parte="particular",
    ...     via_dje=False,
    ... ), hoje=date(2026, 5, 22))
    >>> r.dies_a_quo
    datetime.date(2026, 5, 22)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

ParteType = Literal["particular", "fazenda", "mp", "defensoria"]
TipoDia = Literal["uteis", "corridos"]
Alerta = Literal["URGENTE", "ATENCAO", "NORMAL"]


FERIADOS_FIXOS_NACIONAIS: dict[tuple[int, int], str] = {
    (1, 1): "Confraternizacao Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independencia",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamacao da Republica",
    (11, 20): "Consciencia Negra",
    (12, 25): "Natal",
}


def _easter_date(year: int) -> date:
    """Computus de Gauss/Meeus para data da Pascoa."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def feriados_moveis(year: int) -> dict[date, str]:
    """Feriados moveis baseados na Pascoa."""
    easter = _easter_date(year)
    return {
        easter - timedelta(days=48): "Carnaval (segunda)",
        easter - timedelta(days=47): "Carnaval (terca)",
        easter - timedelta(days=3): "Quinta-feira Santa",
        easter - timedelta(days=2): "Sexta-feira da Paixao",
        easter + timedelta(days=60): "Corpus Christi",
    }


def is_recesso_forense_tjpr(d: date) -> bool:
    """Recesso forense TJPR: 20 dez a 20 jan."""
    if d.month == 12 and d.day >= 20:
        return True
    if d.month == 1 and d.day <= 20:
        return True
    return False


def is_feriado(d: date) -> bool:
    if (d.month, d.day) in FERIADOS_FIXOS_NACIONAIS:
        return True
    if d in feriados_moveis(d.year):
        return True
    if is_recesso_forense_tjpr(d):
        return True
    return False


def is_dia_util(d: date) -> bool:
    """Dia util = nao final-de-semana e nao feriado."""
    if d.weekday() >= 5:
        return False
    if is_feriado(d):
        return False
    return True


def proximo_dia_util(d: date) -> date:
    """Proximo dia util >= d."""
    cur = d
    while not is_dia_util(cur):
        cur += timedelta(days=1)
    return cur


def soma_dias_uteis(start: date, n_dias: int) -> date:
    """Data apos N dias uteis a partir de start."""
    if n_dias <= 0:
        return start
    cur = start
    count = 0
    while count < n_dias:
        cur += timedelta(days=1)
        if is_dia_util(cur):
            count += 1
    return cur


def conta_dias_uteis_entre(start: date, end: date) -> int:
    """Conta dias uteis entre start (exclusivo) e end (inclusivo)."""
    if end <= start:
        return 0
    cur = start + timedelta(days=1)
    count = 0
    while cur <= end:
        if is_dia_util(cur):
            count += 1
        cur += timedelta(days=1)
    return count


@dataclass(frozen=True)
class PrazoInput:
    data_publicacao: date
    prazo_dias: int
    tipo_dia: TipoDia = "uteis"
    parte: ParteType = "particular"
    via_dje: bool = False


@dataclass(frozen=True)
class PrazoResult:
    data_publicacao: date
    data_intimacao_considerada: date
    dies_a_quo: date
    dies_ad_quem: date
    dias_uteis_consumidos: int
    dias_uteis_restantes_hoje: int
    alerta: Alerta
    prazo_efetivo_dias: int
    fundamentos_aplicados: tuple[str, ...]


def _aplica_dobro(parte: ParteType, via_dje: bool) -> bool:
    if parte == "particular":
        return False
    if parte == "fazenda" and via_dje:
        return False
    return parte in ("fazenda", "mp", "defensoria")


def calcular_prazo(inp: PrazoInput, hoje: date | None = None) -> PrazoResult:
    """Calcula prazo processual segundo CPC/2015.

    Args:
        inp: Entrada estruturada.
        hoje: Data atual (default = date.today()). Util para testes deterministicos.
    """
    if hoje is None:
        hoje = date.today()

    fundamentos: list[str] = [
        "Art. 219 CPC/2015 (dias uteis)" if inp.tipo_dia == "uteis" else "Dias corridos"
    ]

    if inp.via_dje:
        data_intimacao = proximo_dia_util(inp.data_publicacao + timedelta(days=1))
        fundamentos.append("Art. 231 #1 CPC (intimacao eletronica)")
    else:
        data_intimacao = inp.data_publicacao

    dies_a_quo = proximo_dia_util(data_intimacao + timedelta(days=1))
    fundamentos.append("Art. 224 CPC (dies a quo)")

    prazo_efetivo = inp.prazo_dias
    if _aplica_dobro(inp.parte, inp.via_dje):
        prazo_efetivo = inp.prazo_dias * 2
        if inp.parte == "fazenda":
            fundamentos.append("Art. 183 CPC (Fazenda em dobro)")
        elif inp.parte == "mp":
            fundamentos.append("Art. 180 CPC (MP em dobro)")
        elif inp.parte == "defensoria":
            fundamentos.append("Art. 186 CPC (Defensoria em dobro)")

    if inp.tipo_dia == "uteis":
        dies_ad_quem = soma_dias_uteis(dies_a_quo, prazo_efetivo - 1)
    else:
        dies_ad_quem = dies_a_quo + timedelta(days=prazo_efetivo - 1)

    if hoje < dies_a_quo:
        consumidos = 0
        restantes = conta_dias_uteis_entre(dies_a_quo - timedelta(days=1), dies_ad_quem)
    elif hoje > dies_ad_quem:
        consumidos = prazo_efetivo
        restantes = 0
    else:
        consumidos = conta_dias_uteis_entre(dies_a_quo - timedelta(days=1), hoje)
        restantes = conta_dias_uteis_entre(hoje, dies_ad_quem)

    if restantes <= 3:
        alerta: Alerta = "URGENTE"
    elif restantes <= 7:
        alerta = "ATENCAO"
    else:
        alerta = "NORMAL"

    return PrazoResult(
        data_publicacao=inp.data_publicacao,
        data_intimacao_considerada=data_intimacao,
        dies_a_quo=dies_a_quo,
        dies_ad_quem=dies_ad_quem,
        dias_uteis_consumidos=consumidos,
        dias_uteis_restantes_hoje=restantes,
        alerta=alerta,
        prazo_efetivo_dias=prazo_efetivo,
        fundamentos_aplicados=tuple(fundamentos),
    )
