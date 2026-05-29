"""Deteccao de clausulas de risco em contratos de aquisicao.

Faz varredura por regex/keyword em contratos de M&A (em PT ou EN) e
sinaliza tanto a presenca de clausulas sensiveis (change of control,
MAC, cap de indenizacao, sobrevivencia de R&W, non-compete, earn-out)
quanto a AUSENCIA de protecoes que sao red flags por si so (sem MAC,
sem cap de indenizacao).

Roda DEPOIS do pii-redactor-br — nao loga input bruto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

TipoRedFlag = Literal[
    "change_of_control",
    "mac",
    "indemnification_cap",
    "rw_survival",
    "non_compete",
    "earn_out",
    "mac_ausente",
    "sem_cap_indenizacao",
]

Severidade = Literal["baixa", "media", "alta"]

_TRECHO_RAIO = 80  # caracteres de cada lado do match (~160 no total).

CHANGE_OF_CONTROL_RE = re.compile(
    r"change\s+of\s+control|mudan[çc]a\s+de\s+controle", re.IGNORECASE
)
MAC_RE = re.compile(
    r"material\s+adverse\s+change|material\s+adverse\s+effect|"
    r"efeito\s+(?:material\s+)?adverso\s+relevante|\bMAC\b|\bMAE\b",
    re.IGNORECASE,
)
INDEMNIFICATION_CAP_RE = re.compile(
    r"(?:indemnif\w*|indeniza[çc]\w*).{0,60}?(?:cap|limit\w*|teto|limita\w*)|"
    r"(?:cap|teto|limit\w*).{0,60}?(?:indemnif\w*|indeniza[çc]\w*)",
    re.IGNORECASE | re.DOTALL,
)
RW_SURVIVAL_RE = re.compile(
    r"survival\s+(?:period\s+)?of.{0,40}?(?:representations?|warrant\w*)|"
    r"representations?\s+and\s+warrant\w*.{0,40}?surviv\w*|"
    r"(?:sobreviv\w*|prazo\s+de\s+sobreviv\w*).{0,60}?(?:declara[çc]\w*|garantia)",
    re.IGNORECASE | re.DOTALL,
)
NON_COMPETE_RE = re.compile(
    r"non[\-\s]?compet\w*|n[ãa]o[\-\s]?concorr\w*|cl[aá]usula\s+de\s+n[ãa]o[\-\s]?concorr\w*",
    re.IGNORECASE,
)
EARN_OUT_RE = re.compile(r"earn[\-\s]?out|pagamento\s+contingente", re.IGNORECASE)


@dataclass(frozen=True)
class RedFlag:
    """Uma sinalizacao de risco encontrada (ou ausencia critica).

    Attributes:
        tipo: Categoria da red flag.
        severidade: Gravidade estimada.
        trecho: Trecho de ~160 chars ao redor do match (vazio se ausencia).
        nota: Nota explicativa para o revisor.
    """

    tipo: TipoRedFlag
    severidade: Severidade
    trecho: str
    nota: str


def _extrair_trecho(text: str, match: re.Match[str]) -> str:
    """Recorta ~160 chars centrados no match, normalizando espacos."""
    start = max(0, match.start() - _TRECHO_RAIO)
    end = min(len(text), match.end() + _TRECHO_RAIO)
    return " ".join(text[start:end].split())


def scan_acquisition_contract(text: str) -> tuple[RedFlag, ...]:
    """Varre contrato de aquisicao e retorna red flags detectadas.

    Detecta presencas de clausulas sensiveis e tambem ausencias que
    constituem risco (sem MAC, sem cap de indenizacao). Texto vazio
    retorna apenas as red flags de ausencia.

    Args:
        text: Texto do contrato (ja sem PII).

    Returns:
        Tupla de ``RedFlag`` na ordem: presencas detectadas seguidas
        das ausencias relevantes.
    """
    flags: list[RedFlag] = []
    conteudo = text or ""

    presencas: tuple[tuple[TipoRedFlag, re.Pattern[str], Severidade, str], ...] = (
        (
            "change_of_control",
            CHANGE_OF_CONTROL_RE,
            "alta",
            "Clausula de change of control pode acelerar obrigacoes na aquisicao.",
        ),
        (
            "mac",
            MAC_RE,
            "media",
            "Clausula MAC presente — revisar definicao e gatilhos.",
        ),
        (
            "indemnification_cap",
            INDEMNIFICATION_CAP_RE,
            "media",
            "Cap de indenizacao presente — revisar valor e exclusoes.",
        ),
        (
            "rw_survival",
            RW_SURVIVAL_RE,
            "baixa",
            "Periodo de sobrevivencia de R&W definido — conferir prazo.",
        ),
        (
            "non_compete",
            NON_COMPETE_RE,
            "media",
            "Clausula de non-compete — revisar prazo e abrangencia.",
        ),
        (
            "earn_out",
            EARN_OUT_RE,
            "media",
            "Earn-out presente — risco de disputa sobre metricas/apuracao.",
        ),
    )

    tem_mac = False
    tem_cap = False
    for tipo, pattern, severidade, nota in presencas:
        match = pattern.search(conteudo)
        if match is None:
            continue
        if tipo == "mac":
            tem_mac = True
        if tipo == "indemnification_cap":
            tem_cap = True
        flags.append(
            RedFlag(
                tipo=tipo,
                severidade=severidade,
                trecho=_extrair_trecho(conteudo, match),
                nota=nota,
            )
        )

    if not tem_mac:
        flags.append(
            RedFlag(
                tipo="mac_ausente",
                severidade="media",
                trecho="",
                nota="Ausencia de clausula MAC — comprador sem protecao contra "
                "mudanca adversa relevante entre signing e closing.",
            )
        )
    if not tem_cap:
        flags.append(
            RedFlag(
                tipo="sem_cap_indenizacao",
                severidade="alta",
                trecho="",
                nota="Ausencia de cap de indenizacao — exposicao ilimitada do "
                "vendedor (ou comprador) a passivos.",
            )
        )

    return tuple(flags)
