"""Checklist de due diligence (DD) BR com deteccao de gaps.

Cobre as cinco areas tipicas de DD em M&A no Brasil: trabalhista,
fiscal, ambiental, contratual e societario. Cada item referencia o
documento/certidao comprobatoria (ex.: CND Receita Federal, FGTS/CRF,
CVM, Junta Comercial) e carrega um status.

Roda DEPOIS do pii-redactor-br — nao loga input bruto.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

AreaDD = Literal["trabalhista", "fiscal", "ambiental", "contratual", "societario"]

StatusItem = Literal["pendente", "ok", "alerta", "critico", "nao_aplicavel"]


@dataclass(frozen=True)
class ItemDD:
    """Um item do checklist de due diligence.

    Attributes:
        area: Area da DD.
        descricao: Descricao curta do item.
        obrigatorio: Se o item e exigido para concluir a DD.
        referencia: Documento/orgao comprobatorio.
        status: Status atual do item.
    """

    area: AreaDD
    descricao: str
    obrigatorio: bool
    referencia: str
    status: StatusItem = "pendente"


def _itens_padrao() -> tuple[ItemDD, ...]:
    """Constroi o conjunto padrao de itens de DD BR."""
    return (
        # Trabalhista
        ItemDD("trabalhista", "Certidao negativa de debitos trabalhistas", True, "CNDT/TST"),
        ItemDD("trabalhista", "Regularidade do FGTS", True, "FGTS/CRF"),
        ItemDD("trabalhista", "Passivo de acoes trabalhistas", True, "Justica do Trabalho"),
        # Fiscal
        ItemDD("fiscal", "Certidao de tributos federais", True, "CND Receita Federal"),
        ItemDD("fiscal", "Certidao de tributos estaduais", True, "CND SEFAZ Estadual"),
        ItemDD("fiscal", "Certidao de tributos municipais", False, "CND Prefeitura"),
        # Ambiental
        ItemDD("ambiental", "Licencas ambientais de operacao", True, "Licenca Ambiental"),
        ItemDD("ambiental", "Passivos e autuacoes ambientais", False, "IBAMA/Orgao estadual"),
        # Contratual
        ItemDD("contratual", "Contratos comerciais relevantes", True, "Contratos Comerciais"),
        ItemDD("contratual", "Clausulas de change of control", False, "Contratos Comerciais"),
        # Societario
        ItemDD("societario", "Contrato/estatuto social atualizado", True, "Junta Comercial"),
        ItemDD("societario", "Atos societarios registrados", True, "Junta Comercial"),
        ItemDD("societario", "Registro CVM (se companhia aberta)", False, "CVM"),
    )


def checklist_padrao() -> DueDiligenceChecklist:
    """Cria um ``DueDiligenceChecklist`` com o conjunto padrao de itens.

    Returns:
        Checklist pronto para uso, todos os itens em ``pendente``.
    """
    return DueDiligenceChecklist(list(_itens_padrao()))


class DueDiligenceChecklist:
    """Colecao mutavel de itens de DD com analise de cobertura."""

    def __init__(self, itens: list[ItemDD] | None = None) -> None:
        """Inicializa o checklist.

        Args:
            itens: Lista inicial de itens; vazia se None.
        """
        self._itens: list[ItemDD] = list(itens) if itens is not None else []

    @property
    def itens(self) -> tuple[ItemDD, ...]:
        """Tupla imutavel dos itens atuais."""
        return tuple(self._itens)

    def add(self, item: ItemDD) -> None:
        """Adiciona um item ao checklist."""
        self._itens.append(item)

    def set_status(self, area: AreaDD, descricao: str, status: StatusItem) -> bool:
        """Atualiza o status de um item por (area, descricao).

        Args:
            area: Area do item.
            descricao: Descricao exata do item.
            status: Novo status.

        Returns:
            True se algum item foi atualizado, False caso contrario.
        """
        atualizado = False
        for i, item in enumerate(self._itens):
            if item.area == area and item.descricao == descricao:
                self._itens[i] = replace(item, status=status)
                atualizado = True
        return atualizado

    def gaps(self) -> tuple[ItemDD, ...]:
        """Retorna itens obrigatorios ainda pendentes ou criticos.

        Returns:
            Tupla de itens que representam lacunas/risco na DD.
        """
        return tuple(
            item
            for item in self._itens
            if item.obrigatorio and item.status in ("pendente", "critico")
        )

    def score(self) -> float:
        """Fracao de itens obrigatorios aplicaveis marcados como ``ok``.

        Itens obrigatorios marcados como ``nao_aplicavel`` saem do
        denominador. Retorna 1.0 se nao houver item aplicavel.

        Returns:
            Score em 0.0..1.0.
        """
        aplicaveis = [
            item for item in self._itens if item.obrigatorio and item.status != "nao_aplicavel"
        ]
        if not aplicaveis:
            return 1.0
        ok = sum(1 for item in aplicaveis if item.status == "ok")
        return ok / len(aplicaveis)

    def resumo_por_area(self) -> dict[AreaDD, dict[StatusItem, int]]:
        """Conta itens por status em cada area.

        Returns:
            Mapa area -> {status -> contagem}.
        """
        resumo: dict[AreaDD, dict[StatusItem, int]] = {}
        for item in self._itens:
            por_status = resumo.setdefault(item.area, {})
            por_status[item.status] = por_status.get(item.status, 0) + 1
        return resumo
