"""Playbook de comunicacao de incidente de seguranca a ANPD (Art. 48 LGPD).

Gera plano de resposta determinístico para incidentes que possam acarretar
risco ou dano relevante aos titulares (Art. 48 LGPD). Avalia severidade,
calcula prazo de comunicacao a ANPD em dias uteis e monta checklist pt-BR.

Roda DEPOIS do pii-redactor-br — nao loga input bruto.

Referencias:
- Art. 48: comunicacao de incidente a ANPD e ao titular
- Art. 48 paragrafo 1: conteudo minimo da comunicacao
- Orientacao ANPD: prazo de 2 dias uteis a partir da ciencia
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from legalops.lgpd_specifics import PRAZO_INCIDENTE_ANPD_DIAS, TipoDado

Severidade = Literal["baixa", "media", "alta", "critica"]

# Limiares de num_titulares para escalonamento de severidade.
_LIMIAR_TITULARES_MEDIO: int = 100
_LIMIAR_TITULARES_ALTO: int = 1000

# Dados que elevam a severidade por natureza (Art. 11 / Art. 14).
_DADOS_AGRAVANTES: frozenset[TipoDado] = frozenset({TipoDado.SENSIVEL, TipoDado.CRIANCA})

_NIVEIS: tuple[Severidade, ...] = ("baixa", "media", "alta", "critica")


@dataclass(frozen=True)
class Incidente:
    """Incidente de seguranca com dados pessoais.

    Attributes:
        incidente_id: Identificador interno do incidente.
        descricao: Descricao curta (ja redigida sem PII bruto).
        data_descoberta: Data da ciencia do incidente.
        dados_afetados: Categorias de dados envolvidas.
        num_titulares: Numero estimado de titulares afetados.
        vazamento_confirmado: Se ha exfiltracao/vazamento confirmado.
    """

    incidente_id: str
    descricao: str
    data_descoberta: date
    dados_afetados: tuple[TipoDado, ...]
    num_titulares: int
    vazamento_confirmado: bool


@dataclass(frozen=True)
class PlanoComunicacao:
    """Plano de resposta a incidente segundo Art. 48 LGPD.

    Attributes:
        incidente_id: Identificador do incidente.
        severidade: Severidade avaliada.
        comunicar_anpd: Se ha dever de comunicar a ANPD.
        comunicar_titulares: Se ha dever de comunicar os titulares.
        prazo_anpd: Data-limite para comunicar a ANPD (None se nao aplicavel).
        dias_restantes: Dias corridos ate o prazo a partir de ``hoje``.
        passos: Checklist ordenado de acoes em pt-BR.
    """

    incidente_id: str
    severidade: Severidade
    comunicar_anpd: bool
    comunicar_titulares: bool
    prazo_anpd: date | None
    dias_restantes: int | None
    passos: tuple[str, ...]


def _eleva(nivel: Severidade, passos: int = 1) -> Severidade:
    """Eleva a severidade em ``passos`` niveis, limitado a ``critica``."""
    idx = min(_NIVEIS.index(nivel) + passos, len(_NIVEIS) - 1)
    return _NIVEIS[idx]


def avaliar_severidade(inc: Incidente) -> Severidade:
    """Avalia a severidade de um incidente por heuristica determinística.

    Regras (cumulativas, escalonando a partir de ``baixa``):
        - Dados sensiveis ou de crianca (Art. 11 / Art. 14): +1 nivel.
        - num_titulares >= 100: +1 nivel; >= 1000: +1 nivel adicional.
        - vazamento_confirmado: +1 nivel.

    Args:
        inc: Incidente a avaliar.

    Returns:
        Severidade resultante em {baixa, media, alta, critica}.
    """
    nivel: Severidade = "baixa"
    if any(d in _DADOS_AGRAVANTES for d in inc.dados_afetados):
        nivel = _eleva(nivel)
    if inc.num_titulares >= _LIMIAR_TITULARES_ALTO:
        nivel = _eleva(nivel, 2)
    elif inc.num_titulares >= _LIMIAR_TITULARES_MEDIO:
        nivel = _eleva(nivel)
    if inc.vazamento_confirmado:
        nivel = _eleva(nivel)
    return nivel


def _add_dias_uteis(inicio: date, dias: int) -> date:
    """Soma ``dias`` dias uteis a ``inicio``, pulando sabado e domingo.

    Args:
        inicio: Data de partida.
        dias: Quantidade de dias uteis a somar (>= 0).

    Returns:
        Data resultante apos pular fins de semana.
    """
    atual = inicio
    restantes = dias
    while restantes > 0:
        atual += timedelta(days=1)
        if atual.weekday() < 5:  # 0=segunda .. 4=sexta
            restantes -= 1
    return atual


def conteudo_minimo_comunicacao() -> tuple[str, ...]:
    """Retorna o conteudo minimo da comunicacao a ANPD (Art. 48 paragrafo 1).

    Returns:
        Tupla ordenada com os itens obrigatorios da comunicacao.
    """
    return (
        "Descricao da natureza dos dados pessoais afetados (Art. 48 par. 1 I).",
        "Informacoes sobre os titulares envolvidos (Art. 48 par. 1 II).",
        "Indicacao das medidas tecnicas e de seguranca adotadas (Art. 48 par. 1 III).",
        "Riscos relacionados ao incidente (Art. 48 par. 1 IV).",
        "Motivos da demora, caso a comunicacao nao seja imediata (Art. 48 par. 1 V).",
        "Medidas adotadas ou a adotar para reverter ou mitigar os efeitos (Art. 48 par. 1 VI).",
    )


def gerar_plano(inc: Incidente, hoje: date | None = None) -> PlanoComunicacao:
    """Gera o plano de comunicacao do incidente conforme Art. 48 LGPD.

    Comunica-se a ANPD quando o incidente pode acarretar risco ou dano
    relevante (severidade >= media). Comunicam-se os titulares para
    severidade alta ou critica. O prazo a ANPD e ``data_descoberta`` mais
    ``PRAZO_INCIDENTE_ANPD_DIAS`` dias uteis.

    Args:
        inc: Incidente a tratar.
        hoje: Data de referencia para ``dias_restantes`` (default: hoje real).

    Returns:
        Plano de comunicacao com flags, prazo e checklist de passos.
    """
    ref = hoje if hoje is not None else date.today()
    severidade = avaliar_severidade(inc)

    comunicar_anpd = severidade in ("media", "alta", "critica")
    comunicar_titulares = severidade in ("alta", "critica")

    prazo_anpd: date | None = None
    dias_restantes: int | None = None
    if comunicar_anpd:
        prazo_anpd = _add_dias_uteis(inc.data_descoberta, PRAZO_INCIDENTE_ANPD_DIAS)
        dias_restantes = (prazo_anpd - ref).days

    passos: list[str] = [
        "Conter o incidente e preservar evidencias (logs, escopo, vetor).",
        "Avaliar o risco e o dano relevante aos titulares (Art. 48).",
    ]
    if comunicar_anpd:
        passos.append(
            "Comunicar a ANPD em prazo razoavel (2 dias uteis) com o conteudo "
            "minimo do Art. 48 par. 1."
        )
    if comunicar_titulares:
        passos.append("Comunicar os titulares afetados de forma clara (Art. 48).")
    passos.append("Registrar o incidente e as medidas em registro interno (Art. 37).")
    passos.append("Revisar controles de seguranca para prevenir recorrencia (Art. 46).")

    return PlanoComunicacao(
        incidente_id=inc.incidente_id,
        severidade=severidade,
        comunicar_anpd=comunicar_anpd,
        comunicar_titulares=comunicar_titulares,
        prazo_anpd=prazo_anpd,
        dias_restantes=dias_restantes,
        passos=tuple(passos),
    )
