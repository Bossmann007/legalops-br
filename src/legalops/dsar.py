"""DSAR Responder — resposta a requisicoes de titulares (Art. 18/19 LGPD).

Classifica requisicoes em texto livre em um dos direitos do titular (Art. 18) e
calcula prazo de resposta (Art. 19 - 15 dias), status e um texto-padrao em
pt-BR para resposta.

Deterministico, stdlib only. Roda DEPOIS do pii-redactor — assume texto sem PII
bruto. ``titular_ref`` deve ser pseudonimo opaco, nunca PII real.

Uso:
    >>> from datetime import date
    >>> from legalops.dsar import DSARRequest, classify_request, processar_dsar
    >>> classify_request("quero acessar meus dados")
    'acesso'
    >>> req = DSARRequest("r1", "acesso", date(2026, 1, 1), "titular-abc")
    >>> resp = processar_dsar(req, hoje=date(2026, 1, 5))
    >>> resp.dias_restantes
    11
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from legalops.lgpd_specifics import (
    DIREITOS_TITULAR,
    PRAZO_RESPOSTA_TITULAR_DIAS,
    DireitoTitular,
)

__all__ = [
    "DSARError",
    "DSARRequest",
    "DSARResponse",
    "classify_request",
    "processar_dsar",
]

StatusDSAR = Literal["no_prazo", "vence_hoje", "em_atraso"]


class DSARError(ValueError):
    """Erro de processamento de requisicao DSAR (codigo de direito invalido)."""


# Padroes de classificacao por palavra-chave. Ordem importa: padroes mais
# especificos primeiro para evitar captura prematura por um padrao generico.
_CLASSIFICACAO_RE: list[tuple[str, re.Pattern[str]]] = [
    (
        "revogacao_consentimento",
        re.compile(
            r"\brevogar?\b.*\bconsentimento\b|\bretirar\b.*\bconsentimento\b",
            re.IGNORECASE,
        ),
    ),
    (
        "portabilidade",
        re.compile(
            r"\bportar?\b|\bportabilidade\b|\btransferir\b|\btransferencia\b",
            re.IGNORECASE,
        ),
    ),
    (
        "eliminacao",
        re.compile(r"\bapag\w*\b|\belimin\w*\b|\bdeletar?\b|\bexclu\w*\b", re.IGNORECASE),
    ),
    (
        "anonimizacao",
        re.compile(r"\banonimiz\w*\b|\bbloquear?\b|\bbloqueio\b", re.IGNORECASE),
    ),
    (
        "correcao",
        re.compile(
            r"\bcorrig\w*\b|\bcorre[çc][ãa]o\b|\bretificar?\b|\batualizar?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "confirmacao",
        re.compile(
            r"\bconfirmar?\b|\bconfirma[çc][ãa]o\b|\bexiste\b.*\btratamento\b",
            re.IGNORECASE,
        ),
    ),
    (
        "oposicao",
        re.compile(r"\bme\s+opon\w*\b|\boposi[çc][ãa]o\b|\boponho\b", re.IGNORECASE),
    ),
    (
        "informacao_compartilhamento",
        re.compile(r"\bcompartilh\w*\b", re.IGNORECASE),
    ),
    (
        "acesso",
        re.compile(
            r"\bacessar?\b|\bacesso\b|\bc[óo]pia\b|\bquais?\s+dados\b",
            re.IGNORECASE,
        ),
    ),
]


def _buscar_direito(codigo: str) -> DireitoTitular | None:
    for d in DIREITOS_TITULAR:
        if d.codigo == codigo:
            return d
    return None


def classify_request(texto: str) -> str:
    """Mapeia uma requisicao em texto livre para um codigo de direito (Art. 18).

    Args:
        texto: Texto livre da requisicao do titular (ja sem PII bruto).

    Returns:
        O ``codigo`` do direito correspondente (ex: ``"acesso"``), ou ``""``
        se nao for possivel classificar.
    """
    if not texto or not texto.strip():
        return ""
    for codigo, pattern in _CLASSIFICACAO_RE:
        if pattern.search(texto):
            return codigo
    return ""


@dataclass(frozen=True)
class DSARRequest:
    """Requisicao de um titular de dados (Art. 18 LGPD).

    Attributes:
        request_id: Identificador opaco da requisicao.
        codigo_direito: Codigo do direito invocado (Art. 18).
        data_recebimento: Data em que a requisicao foi recebida.
        titular_ref: Pseudonimo opaco do titular (NUNCA PII real).
    """

    request_id: str
    codigo_direito: str
    data_recebimento: date
    titular_ref: str


@dataclass(frozen=True)
class DSARResponse:
    """Resposta calculada para uma requisicao de titular (Art. 19 LGPD)."""

    request_id: str
    codigo_direito: str
    artigo: str
    prazo_final: date
    dias_restantes: int
    status: StatusDSAR
    texto_resposta: str


def _classificar_status(dias_restantes: int) -> StatusDSAR:
    if dias_restantes < 0:
        return "em_atraso"
    if dias_restantes == 0:
        return "vence_hoje"
    return "no_prazo"


def _montar_texto(direito: DireitoTitular, prazo_final: date, status: StatusDSAR) -> str:
    nota_status = {
        "no_prazo": "A requisicao esta dentro do prazo legal.",
        "vence_hoje": "ATENCAO: o prazo legal vence hoje.",
        "em_atraso": "ATENCAO: o prazo legal foi ultrapassado.",
    }[status]
    return (
        f"Prezado(a) titular,\n\n"
        f"Recebemos sua requisicao referente ao direito de '{direito.codigo}' "
        f"({direito.artigo}): {direito.descricao}\n\n"
        f"Nos termos do Art. 19 da LGPD, sua solicitacao sera respondida ate "
        f"{prazo_final.isoformat()} (prazo de {PRAZO_RESPOSTA_TITULAR_DIAS} dias).\n"
        f"{nota_status}\n\n"
        f"Atenciosamente,\nEncarregado de Protecao de Dados (DPO)."
    )


def processar_dsar(req: DSARRequest, hoje: date | None = None) -> DSARResponse:
    """Processa uma requisicao DSAR e calcula prazo, status e texto de resposta.

    Args:
        req: Requisicao do titular.
        hoje: Data de referencia (default: ``date.today()``).

    Returns:
        ``DSARResponse`` com prazo final (Art. 19), dias restantes, status e
        texto-padrao em pt-BR.

    Raises:
        DSARError: Se ``req.codigo_direito`` nao corresponder a um direito
            conhecido em ``DIREITOS_TITULAR``.
    """
    direito = _buscar_direito(req.codigo_direito)
    if direito is None:
        raise DSARError(f"Codigo de direito desconhecido: '{req.codigo_direito}'")

    ref = hoje if hoje is not None else date.today()
    prazo_final = req.data_recebimento + timedelta(days=direito.prazo_resposta_dias)
    dias_restantes = (prazo_final - ref).days
    status = _classificar_status(dias_restantes)

    return DSARResponse(
        request_id=req.request_id,
        codigo_direito=req.codigo_direito,
        artigo=direito.artigo,
        prazo_final=prazo_final,
        dias_restantes=dias_restantes,
        status=status,
        texto_resposta=_montar_texto(direito, prazo_final, status),
    )
