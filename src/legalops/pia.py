"""PIA / RIPD — Relatorio de Impacto a Protecao de Dados (Art. 38 LGPD).

Avalia uma operacao de tratamento e produz um RIPD com riscos de privacidade,
score ponderado, nivel de risco e flag de conformidade.

Deterministico, stdlib only. Reusa ``validar_operacao`` de ``lgpd_specifics``.

Uso:
    >>> from legalops.lgpd_specifics import BaseLegal, OperacaoTratamento, TipoDado
    >>> from legalops.pia import avaliar_ripd
    >>> op = OperacaoTratamento(
    ...     tipo_operacao="coleta",
    ...     tipos_dados=[TipoDado.SENSIVEL],
    ...     base_legal=BaseLegal.CONSENTIMENTO,
    ...     finalidade="pesquisa clinica",
    ... )
    >>> ripd = avaliar_ripd(op)
    >>> ripd.nivel
    'alto'
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from legalops.lgpd_specifics import (
    BaseLegal,
    OperacaoTratamento,
    TipoDado,
    validar_operacao,
)

__all__ = [
    "RIPD",
    "RiscoPrivacidade",
    "Severidade",
    "avaliar_ripd",
]

Severidade = Literal["baixo", "medio", "alto", "critico"]

# Pesos por severidade para o score ponderado.
_PESO: dict[Severidade, int] = {"baixo": 1, "medio": 3, "alto": 5, "critico": 8}

# Limiares de score para classificar o nivel do RIPD.
_NIVEL_MEDIO = 3
_NIVEL_ALTO = 6
_NIVEL_CRITICO = 10

# Ordem de severidade para combinar com a classificacao por score.
_ORDEM: tuple[Severidade, ...] = ("baixo", "medio", "alto", "critico")


@dataclass(frozen=True)
class RiscoPrivacidade:
    """Um risco de privacidade identificado numa operacao de tratamento."""

    descricao: str
    severidade: Severidade
    recomendacao: str
    artigo: str


@dataclass(frozen=True)
class RIPD:
    """Relatorio de Impacto a Protecao de Dados (Art. 38)."""

    operacao: str
    riscos: tuple[RiscoPrivacidade, ...]
    score: int
    nivel: Severidade
    conforme: bool


def _nivel_por_score(score: int) -> Severidade:
    if score >= _NIVEL_CRITICO:
        return "critico"
    if score >= _NIVEL_ALTO:
        return "alto"
    if score >= _NIVEL_MEDIO:
        return "medio"
    return "baixo"


def _combinar_nivel(score: int, riscos: tuple[RiscoPrivacidade, ...]) -> Severidade:
    """Nivel = o maior entre a classificacao por score e o pior risco isolado.

    Um RIPD com um unico risco 'alto' nao deve ser classificado 'medio' so
    porque o score acumulado ficou abaixo do limiar.
    """
    por_score = _nivel_por_score(score)
    if not riscos:
        return por_score
    pior = max((r.severidade for r in riscos), key=_ORDEM.index)
    return max((por_score, pior), key=_ORDEM.index)


def avaliar_ripd(op: OperacaoTratamento) -> RIPD:
    """Avalia uma operacao de tratamento e produz um RIPD (Art. 38).

    Emite um ``RiscoPrivacidade`` curado por categoria de dado, base legal e
    principios (finalidade, necessidade). Cada risco aparece uma unica vez -
    nao ha conversao dos avisos genericos de ``validar_operacao`` para evitar
    listar a mesma questao duas vezes com severidades conflitantes.

    Args:
        op: Operacao de tratamento a avaliar.

    Returns:
        ``RIPD`` com riscos, score ponderado, nivel e flag de conformidade.
        ``conforme`` exige ``validar_operacao`` valido E nenhum risco critico.
    """
    valido, _avisos = validar_operacao(op)
    riscos: list[RiscoPrivacidade] = []

    # Art. 6 I - finalidade obrigatoria.
    if not op.finalidade or not op.finalidade.strip():
        riscos.append(
            RiscoPrivacidade(
                descricao="Finalidade do tratamento ausente ou nao especifica.",
                severidade="medio",
                recomendacao=(
                    "Definir finalidade especifica, explicita e informada ao titular (Art. 6 I)."
                ),
                artigo="Art. 6 I",
            )
        )

    tem_sensivel = TipoDado.SENSIVEL in op.tipos_dados
    tem_crianca = TipoDado.CRIANCA in op.tipos_dados

    # Dados sensiveis (Art. 11) -> alto.
    if tem_sensivel:
        riscos.append(
            RiscoPrivacidade(
                descricao="Tratamento de dados pessoais sensiveis.",
                severidade="alto",
                recomendacao=(
                    "Garantir base legal compativel (Art. 11) e medidas reforcadas de seguranca."
                ),
                artigo="Art. 11",
            )
        )

    # Dados de crianca (Art. 14) -> alto.
    if tem_crianca:
        riscos.append(
            RiscoPrivacidade(
                descricao="Tratamento de dados de criancas e adolescentes.",
                severidade="alto",
                recomendacao="Obter consentimento parental especifico e em destaque.",
                artigo="Art. 14",
            )
        )

    # Legitimo interesse + dado sensivel -> critico.
    if tem_sensivel and op.base_legal == BaseLegal.LEGITIMO_INTERESSE:
        riscos.append(
            RiscoPrivacidade(
                descricao=(
                    "Base 'legitimo interesse' usada para dados sensiveis - vedada pelo Art. 11."
                ),
                severidade="critico",
                recomendacao="Substituir por base legal valida do Art. 11.",
                artigo="Art. 11",
            )
        )

    # Falta de necessidade (Art. 6 III) -> medio.
    if not op.necessario:
        riscos.append(
            RiscoPrivacidade(
                descricao="Tratamento alem do minimo necessario.",
                severidade="medio",
                recomendacao="Limitar o tratamento ao minimo necessario (minimizacao).",
                artigo="Art. 6 III",
            )
        )

    riscos_t = tuple(riscos)
    score = sum(_PESO[r.severidade] for r in riscos_t)
    nivel = _combinar_nivel(score, riscos_t)
    tem_critico = any(r.severidade == "critico" for r in riscos_t)
    conforme = valido and not tem_critico

    return RIPD(
        operacao=op.tipo_operacao,
        riscos=riscos_t,
        score=score,
        nivel=nivel,
        conforme=conforme,
    )
