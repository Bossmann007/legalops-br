"""Classificacao e auditoria de completude de data room.

Heuristicas de keyword/regex para classificar documentos de um data
room de M&A e auditar a presenca das categorias requeridas.

Roda DEPOIS do pii-redactor-br — nao loga input bruto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

TipoDoc = Literal[
    "contrato_social",
    "balanco",
    "certidao",
    "contrato_comercial",
    "processo_judicial",
    "licenca_ambiental",
    "folha_pagamento",
    "outros",
]

# Patterns ordenados por especificidade.
CONTRATO_SOCIAL_RE = re.compile(
    r"\bcontrato\s+social\b|\bestatuto\s+social\b|\baltera[çc][ãa]o\s+contratual\b",
    re.IGNORECASE,
)
BALANCO_RE = re.compile(
    r"\bbalan[çc]o\s+patrimonial\b|\bdemonstra[çc][ãa]o\s+(?:do\s+)?resultado\b|\bDRE\b|\bbalancete\b",
    re.IGNORECASE,
)
CERTIDAO_RE = re.compile(
    r"\bcertid[ãa]o\b|\bCND\b|\bCRF\b|\bnegativa\s+de\s+d[eé]bitos\b", re.IGNORECASE
)
PROCESSO_JUDICIAL_RE = re.compile(
    r"\bprocesso\s+judicial\b|\ba[çc][ãa]o\s+judicial\b|\bpeti[çc][ãa]o\s+inicial\b|"
    r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b",
    re.IGNORECASE,
)
LICENCA_AMBIENTAL_RE = re.compile(
    r"\blicen[çc]a\s+ambiental\b|\blicen[çc]a\s+de\s+opera[çc][ãa]o\b|\bIBAMA\b",
    re.IGNORECASE,
)
FOLHA_PAGAMENTO_RE = re.compile(
    r"\bfolha\s+de\s+pagamento\b|\bholerite\b|\bcontracheque\b", re.IGNORECASE
)
CONTRATO_COMERCIAL_RE = re.compile(
    r"\bcontrato\s+(?:de\s+)?(?:presta[çc][ãa]o|fornecimento|compra\s+e\s+venda|"
    r"distribui[çc][ãa]o|comercial)\b",
    re.IGNORECASE,
)


def classify_document(text: str) -> TipoDoc:
    """Classifica um documento de data room por heuristica de keywords.

    A ordem de checagem vai do mais especifico ao mais generico.

    Args:
        text: Conteudo (ja sem PII) ou nome do documento.

    Returns:
        O ``TipoDoc`` detectado, ou ``"outros"`` se nada casar.
    """
    if not text or not text.strip():
        return "outros"
    if CONTRATO_SOCIAL_RE.search(text):
        return "contrato_social"
    if BALANCO_RE.search(text):
        return "balanco"
    if LICENCA_AMBIENTAL_RE.search(text):
        return "licenca_ambiental"
    if FOLHA_PAGAMENTO_RE.search(text):
        return "folha_pagamento"
    if PROCESSO_JUDICIAL_RE.search(text):
        return "processo_judicial"
    if CERTIDAO_RE.search(text):
        return "certidao"
    if CONTRATO_COMERCIAL_RE.search(text):
        return "contrato_comercial"
    return "outros"


@dataclass(frozen=True)
class DataRoomDoc:
    """Um documento indexado no data room.

    Attributes:
        nome: Nome do arquivo/documento.
        tipo: Categoria do documento.
        paginas: Numero de paginas ou None.
    """

    nome: str
    tipo: TipoDoc
    paginas: int | None = None


class DataRoomIndex:
    """Indice de documentos de um data room com auditoria de completude."""

    def __init__(self, docs: list[DataRoomDoc] | None = None) -> None:
        """Inicializa o indice.

        Args:
            docs: Lista inicial de documentos; vazia se None.
        """
        self._docs: list[DataRoomDoc] = list(docs) if docs is not None else []

    @property
    def docs(self) -> tuple[DataRoomDoc, ...]:
        """Tupla imutavel dos documentos indexados."""
        return tuple(self._docs)

    def add(self, doc: DataRoomDoc) -> None:
        """Adiciona um documento ao indice."""
        self._docs.append(doc)

    def por_tipo(self) -> dict[TipoDoc, int]:
        """Conta documentos por categoria.

        Returns:
            Mapa tipo -> contagem (apenas tipos presentes).
        """
        contagem: dict[TipoDoc, int] = {}
        for doc in self._docs:
            contagem[doc.tipo] = contagem.get(doc.tipo, 0) + 1
        return contagem

    def auditar_completude(self, requeridos: tuple[TipoDoc, ...]) -> tuple[TipoDoc, ...]:
        """Retorna categorias requeridas que nao possuem nenhum documento.

        Args:
            requeridos: Categorias que devem estar presentes.

        Returns:
            Tupla de categorias faltantes, na ordem de ``requeridos``,
            sem duplicatas.
        """
        presentes = {doc.tipo for doc in self._docs}
        faltantes: list[TipoDoc] = []
        for tipo in requeridos:
            if tipo not in presentes and tipo not in faltantes:
                faltantes.append(tipo)
        return tuple(faltantes)
