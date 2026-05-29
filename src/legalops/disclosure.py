"""Auxiliar de gaps em disclosure schedule.

Em M&A, cada representacao e garantia (rep & warranty) que exige
qualificacao deve ter item correspondente no disclosure schedule. Este
modulo cruza representacoes com itens do schedule e aponta lacunas e
inconsistencias.

Roda DEPOIS do pii-redactor-br — nao loga input bruto.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Representacao:
    """Uma representacao e garantia do contrato.

    Attributes:
        id: Identificador unico da representacao (ex.: "R-4.1").
        texto: Texto (ja sem PII) da representacao.
        requer_schedule: Se exige item no disclosure schedule.
    """

    id: str
    texto: str
    requer_schedule: bool


@dataclass(frozen=True)
class DisclosureItem:
    """Um item do disclosure schedule.

    Attributes:
        rep_id: Id da representacao qualificada.
        conteudo: Conteudo da divulgacao.
    """

    rep_id: str
    conteudo: str


class DisclosureSchedule:
    """Colecao de itens de disclosure schedule."""

    def __init__(self, items: list[DisclosureItem] | None = None) -> None:
        """Inicializa o schedule.

        Args:
            items: Lista inicial de itens; vazia se None.
        """
        self._items: list[DisclosureItem] = list(items) if items is not None else []

    @property
    def items(self) -> tuple[DisclosureItem, ...]:
        """Tupla imutavel dos itens do schedule."""
        return tuple(self._items)

    def add(self, item: DisclosureItem) -> None:
        """Adiciona um item ao schedule."""
        self._items.append(item)

    def rep_ids(self) -> frozenset[str]:
        """Conjunto de rep_ids cobertos pelo schedule."""
        return frozenset(item.rep_id for item in self._items)


def find_gaps(
    reps: tuple[Representacao, ...], schedule: DisclosureSchedule
) -> tuple[Representacao, ...]:
    """Encontra representacoes que exigem schedule mas nao tem item.

    Args:
        reps: Representacoes do contrato.
        schedule: Disclosure schedule a cruzar.

    Returns:
        Tupla de representacoes com ``requer_schedule`` True e sem item
        correspondente por ``id``/``rep_id``.
    """
    cobertos = schedule.rep_ids()
    return tuple(rep for rep in reps if rep.requer_schedule and rep.id not in cobertos)


def inconsistencias(
    reps: tuple[Representacao, ...], schedule: DisclosureSchedule
) -> tuple[DisclosureItem, ...]:
    """Encontra itens do schedule sem representacao correspondente.

    Args:
        reps: Representacoes do contrato.
        schedule: Disclosure schedule a cruzar.

    Returns:
        Tupla de itens cujo ``rep_id`` nao casa com nenhuma ``Representacao``.
    """
    ids_reps = frozenset(rep.id for rep in reps)
    return tuple(item for item in schedule.items if item.rep_id not in ids_reps)
