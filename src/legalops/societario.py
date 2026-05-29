"""Analise de estrutura societaria brasileira.

Detecta o tipo de sociedade a partir de texto livre (contrato social,
ficha de Junta Comercial), calcula quoruns de deliberacao conforme o
Codigo Civil/2002 (arts. 1.061, 1.071, 1.076) e a Lei 6.404/76 (S/A),
e valida a coerencia das participacoes societarias.

Roda DEPOIS do pii-redactor-br — assume texto sem PII bruto.

Uso:
    >>> from legalops.societario import detect_tipo_sociedade
    >>> detect_tipo_sociedade("Empresa Exemplo Ltda")
    'ltda'
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from legalops.br_validators import is_valid_cnpj

TipoSociedade = Literal[
    "ltda",
    "sa_fechada",
    "sa_aberta",
    "eireli",
    "mei",
    "slu",
    "desconhecido",
]

MateriaDeliberacao = Literal[
    "alteracao_contrato",
    "designacao_administrador",
    "exclusao_socio",
    "dissolucao",
    "operacoes_ordinarias",
]

# Patterns ordenados por especificidade — formas mais especificas primeiro.
SLU_RE = re.compile(r"\bsociedade\s+limitada\s+unipessoal\b|\bslu\b", re.IGNORECASE)
MEI_RE = re.compile(r"\bmicroempreendedor\s+individual\b|\bmei\b", re.IGNORECASE)
EIRELI_RE = re.compile(r"\beireli\b|\bempresa\s+individual\s+de\s+responsabilidade", re.IGNORECASE)
SA_ABERTA_RE = re.compile(
    r"\bcompanhia\s+aberta\b|\bcapital\s+aberto\b|\bcompanhia\s+de\s+capital\s+aberto\b",
    re.IGNORECASE,
)
SA_RE = re.compile(r"\bsociedade\s+an[oô]nima\b|\bcompanhia\b|\bs[\./]?\s?a\.?\b", re.IGNORECASE)
LTDA_RE = re.compile(r"\bltda\.?\b|\bsociedade\s+limitada\b", re.IGNORECASE)


@dataclass(frozen=True)
class Socio:
    """Um socio da sociedade.

    Attributes:
        nome: Nome (ja anonimizado pelo pii-redactor) ou placeholder.
        participacao_pct: Participacao no capital, float 0..100.
        tipo: Papel do socio na sociedade.
    """

    nome: str
    participacao_pct: float
    tipo: Literal["administrador", "quotista", "acionista"] = "quotista"


@dataclass(frozen=True)
class EstruturaSocietaria:
    """Estrutura societaria consolidada.

    Attributes:
        tipo: Tipo da sociedade.
        cnpj: CNPJ (formatado ou so digitos) ou None se desconhecido.
        socios: Tupla imutavel de socios.
        capital_social: Capital social em reais ou None.
    """

    tipo: TipoSociedade
    cnpj: str | None
    socios: tuple[Socio, ...]
    capital_social: float | None


def detect_tipo_sociedade(text: str) -> TipoSociedade:
    """Detecta o tipo de sociedade a partir de texto livre.

    A ordem de checagem segue da forma mais especifica para a mais
    generica (ex.: "Sociedade Limitada Unipessoal" antes de "Ltda").

    Args:
        text: Texto do contrato social ou ficha cadastral.

    Returns:
        O ``TipoSociedade`` detectado, ou ``"desconhecido"`` se nenhum
        padrao casar.
    """
    if not text or not text.strip():
        return "desconhecido"
    if SLU_RE.search(text):
        return "slu"
    if MEI_RE.search(text):
        return "mei"
    if EIRELI_RE.search(text):
        return "eireli"
    if SA_ABERTA_RE.search(text):
        return "sa_aberta"
    if SA_RE.search(text):
        return "sa_fechada"
    if LTDA_RE.search(text):
        return "ltda"
    return "desconhecido"


def quorum_deliberacao(estrutura: EstruturaSocietaria, materia: MateriaDeliberacao) -> float:
    """Retorna o quorum minimo (em %) exigido para a materia.

    Bases legais (Codigo Civil/2002, sociedade limitada):

    - ``alteracao_contrato``: 75% do capital — CC art. 1.076, I c/c
      art. 1.071, V.
    - ``designacao_administrador``: 50% (maioria do capital quando
      socio nomeado em ato separado) — CC art. 1.076, II.
    - ``exclusao_socio``: 50% (maioria do capital social) — CC art.
      1.085 c/c art. 1.030.
    - ``dissolucao``: 75% — CC art. 1.076, I c/c art. 1.071, VI.
    - ``operacoes_ordinarias``: 50% (maioria de votos dos presentes) —
      CC art. 1.072 ss.

    Para S/A (``sa_fechada``/``sa_aberta``) aplica-se a Lei 6.404/76:
    deliberacoes ordinarias por maioria de votos (50%, art. 129) e
    materias relevantes por maioria do capital votante; aqui adotamos
    50% como piso, exceto dissolucao (50%, art. 136).

    Args:
        estrutura: Estrutura societaria avaliada.
        materia: Materia objeto de deliberacao.

    Returns:
        Percentual minimo do capital exigido (0..100).
    """
    is_sa = estrutura.tipo in ("sa_fechada", "sa_aberta")
    if is_sa:
        # Lei 6.404/76: maioria absoluta de votos como piso geral.
        return 50.0

    quoruns: dict[MateriaDeliberacao, float] = {
        "alteracao_contrato": 75.0,
        "designacao_administrador": 50.0,
        "exclusao_socio": 50.0,
        "dissolucao": 75.0,
        "operacoes_ordinarias": 50.0,
    }
    return quoruns[materia]


def validar_participacoes(estrutura: EstruturaSocietaria) -> tuple[str, ...]:
    """Valida coerencia das participacoes societarias.

    Detecta:
    - Soma das participacoes diferente de 100% (tolerancia 0.01).
    - CNPJ invalido (digito verificador).
    - MEI ou SLU com mais de um socio.
    - Participacao individual fora do intervalo 0..100.
    - Sociedade sem socios.

    Args:
        estrutura: Estrutura a validar.

    Returns:
        Tupla de mensagens de problema; vazia se tudo coerente.
    """
    problemas: list[str] = []

    if estrutura.cnpj is not None and not is_valid_cnpj(estrutura.cnpj):
        problemas.append("CNPJ invalido (digito verificador)")

    if not estrutura.socios:
        problemas.append("Sociedade sem socios cadastrados")

    for socio in estrutura.socios:
        if socio.participacao_pct < 0 or socio.participacao_pct > 100:
            problemas.append(
                f"Participacao fora do intervalo 0..100: {socio.nome} ({socio.participacao_pct}%)"
            )

    if estrutura.socios:
        soma = sum(s.participacao_pct for s in estrutura.socios)
        if abs(soma - 100.0) > 0.01:
            problemas.append(f"Soma das participacoes != 100% (atual: {soma}%)")

    if estrutura.tipo in ("mei", "slu") and len(estrutura.socios) > 1:
        problemas.append(
            f"Tipo {estrutura.tipo} nao admite mais de um socio "
            f"({len(estrutura.socios)} cadastrados)"
        )

    return tuple(problemas)
