"""LGPD compliance constants and base-legal classifier for LegalOps BR.

Modulo: constantes estruturadas da LGPD (Lei 13.709/2018) + validador de
operacoes de tratamento de dados pessoais. Usado por agentes para verificar
conformidade antes de executar operacoes.

Referencias:
- Art. 5: definicoes (dado pessoal, dado sensivel)
- Art. 6: principios (finalidade, adequacao, necessidade)
- Art. 7: bases legais para dados comuns
- Art. 11: bases legais para dados sensiveis
- Art. 14: tratamento de dados de criancas e adolescentes
- Art. 18: direitos do titular
- Art. 19: prazo de resposta ao titular (15 dias)
- Art. 48: comunicacao de incidente a ANPD
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class BaseLegal(StrEnum):
    """Bases legais LGPD para tratamento de dados pessoais (Art. 7 e Art. 11)."""

    CONSENTIMENTO = "consentimento"            # Art. 7 I
    OBRIGACAO_LEGAL = "obrigacao_legal"        # Art. 7 II
    POLITICA_PUBLICA = "politica_publica"      # Art. 7 III
    PESQUISA = "pesquisa"                      # Art. 7 IV
    EXECUCAO_CONTRATO = "execucao_contrato"    # Art. 7 V
    EXERCICIO_DIREITO = "exercicio_direito"    # Art. 7 VI
    PROTECAO_VIDA = "protecao_vida"            # Art. 7 VII
    TUTELA_SAUDE = "tutela_saude"              # Art. 7 VIII / Art. 11 II f
    LEGITIMO_INTERESSE = "legitimo_interesse"  # Art. 7 IX
    PROTECAO_CREDITO = "protecao_credito"      # Art. 7 X


class TipoDado(StrEnum):
    """Categorias de dados pessoais conforme LGPD."""

    COMUM = "comum"          # Art. 5 I - dado pessoal
    SENSIVEL = "sensivel"    # Art. 5 II - origem racial, saude, biometria, etc.
    CRIANCA = "crianca"      # Art. 14 - menor de 12 anos


@dataclass(frozen=True)
class DireitoTitular:
    """Art. 18 LGPD - direitos do titular sobre seus dados."""

    codigo: str
    artigo: str
    descricao: str
    prazo_resposta_dias: int = 15  # Art. 19 - prazo padrao


DIREITOS_TITULAR: list[DireitoTitular] = [
    DireitoTitular(
        codigo="confirmacao",
        artigo="Art. 18 I",
        descricao="Confirmacao da existencia de tratamento.",
    ),
    DireitoTitular(
        codigo="acesso",
        artigo="Art. 18 II",
        descricao="Acesso aos dados pessoais tratados.",
    ),
    DireitoTitular(
        codigo="correcao",
        artigo="Art. 18 III",
        descricao="Correcao de dados incompletos, inexatos ou desatualizados.",
    ),
    DireitoTitular(
        codigo="anonimizacao",
        artigo="Art. 18 IV",
        descricao="Anonimizacao, bloqueio ou eliminacao de dados desnecessarios.",
    ),
    DireitoTitular(
        codigo="portabilidade",
        artigo="Art. 18 V",
        descricao="Portabilidade dos dados a outro fornecedor.",
    ),
    DireitoTitular(
        codigo="eliminacao",
        artigo="Art. 18 VI",
        descricao="Eliminacao dos dados pessoais tratados com consentimento.",
    ),
    DireitoTitular(
        codigo="informacao_compartilhamento",
        artigo="Art. 18 VII",
        descricao=(
            "Informacao sobre entidades publicas/privadas com as quais "
            "houve compartilhamento."
        ),
    ),
    DireitoTitular(
        codigo="informacao_consequencias",
        artigo="Art. 18 VIII",
        descricao="Informacao sobre a possibilidade de nao fornecer consentimento e consequencias.",
    ),
    DireitoTitular(
        codigo="revogacao_consentimento",
        artigo="Art. 18 IX",
        descricao="Revogacao do consentimento.",
    ),
    DireitoTitular(
        codigo="oposicao",
        artigo="Art. 18 paragrafo 2",
        descricao=(
            "Oposicao a tratamento realizado com fundamento em hipotese "
            "de dispensa de consentimento."
        ),
    ),
]


@dataclass(frozen=True)
class OperacaoTratamento:
    """Uma operacao de tratamento de dados que precisa de base legal."""

    tipo_operacao: str
    tipos_dados: list[TipoDado] = field(default_factory=list)
    base_legal: BaseLegal = BaseLegal.LEGITIMO_INTERESSE
    finalidade: str = ""
    necessario: bool = True


# Bases legais compativeis com dados sensiveis (Art. 11).
_BASES_SENSIVEIS_VALIDAS: frozenset[BaseLegal] = frozenset(
    {
        BaseLegal.CONSENTIMENTO,
        BaseLegal.TUTELA_SAUDE,
        BaseLegal.EXERCICIO_DIREITO,
        BaseLegal.PROTECAO_VIDA,
        BaseLegal.OBRIGACAO_LEGAL,
    }
)


def validar_operacao(op: OperacaoTratamento) -> tuple[bool, list[str]]:
    """Valida uma operacao de tratamento contra regras LGPD.

    Retorna (valido, avisos). Avisos sao orientacoes para revisao manual.

    Regras aplicadas:
    - Finalidade vazia -> invalido (Art. 6 I)
    - Dados sensiveis (Art. 11) -> exigir base compativel
    - Criancas (Art. 14) -> warn sobre consentimento parental
    - necessario=False -> warn sobre principio da minimizacao (Art. 6 III)
    """
    avisos: list[str] = []
    valido = True

    # Art. 6 I - finalidade obrigatoria
    if not op.finalidade or not op.finalidade.strip():
        avisos.append(
            "Art. 6 I: finalidade do tratamento e obrigatoria e deve ser "
            "especifica, explicita e informada ao titular."
        )
        valido = False

    # Art. 11 - dados sensiveis exigem base legal restrita
    if TipoDado.SENSIVEL in op.tipos_dados:
        if op.base_legal not in _BASES_SENSIVEIS_VALIDAS:
            avisos.append(
                f"Art. 11: dados sensiveis nao podem ser tratados com base "
                f"'{op.base_legal.value}'. Bases validas: "
                f"{sorted(b.value for b in _BASES_SENSIVEIS_VALIDAS)}."
            )
            valido = False

    # Art. 14 - criancas exigem consentimento parental especifico
    if TipoDado.CRIANCA in op.tipos_dados:
        avisos.append(
            "Art. 14: tratamento de dados de crianca exige consentimento "
            "especifico e em destaque dado por pelo menos um dos pais ou "
            "responsavel legal."
        )

    # Art. 6 III - principio da necessidade (minimizacao)
    if not op.necessario:
        avisos.append(
            "Art. 6 III: principio da necessidade - tratamento deve limitar-se "
            "ao minimo necessario para a finalidade."
        )

    return valido, avisos


# Constantes ANPD / prazos LGPD
PRAZO_RESPOSTA_TITULAR_DIAS: int = 15  # Art. 19
PRAZO_INCIDENTE_ANPD_DIAS: int = 2     # Art. 48 - orientacao ANPD: 2 dias uteis
