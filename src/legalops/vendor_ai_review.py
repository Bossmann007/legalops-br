"""Checklist de review de fornecedores de IA terceirizados (LGPD).

Avalia fornecedores de IA (ex.: APIs de modelos, plataformas de inferencia)
contratados por fintechs e e-commerces quanto a conformidade com a LGPD.
Cada item referencia o artigo aplicavel e carrega um status.

Roda DEPOIS do pii-redactor-br — nao loga input bruto.

Referencias:
- Art. 20: decisao automatizada e direito a revisao
- Art. 33: transferencia internacional de dados
- Art. 37: registro das operacoes de tratamento
- Art. 39: operador segue instrucoes do controlador (DPA)
- Art. 41: encarregado (DPO)
- Art. 46: medidas de seguranca
- Art. 48: comunicacao de incidente
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

StatusItem = Literal["pendente", "ok", "alerta", "critico", "nao_aplicavel"]


@dataclass(frozen=True)
class ItemVendorReview:
    """Um item do checklist de review de fornecedor de IA.

    Attributes:
        chave: Identificador estavel do item.
        pergunta: Pergunta de avaliacao em pt-BR.
        artigo: Artigo LGPD aplicavel.
        status: Status atual do item.
        obrigatorio: Se o item e exigido para aprovacao.
    """

    chave: str
    pergunta: str
    artigo: str
    status: StatusItem = "pendente"
    obrigatorio: bool = True


def _itens_padrao() -> tuple[ItemVendorReview, ...]:
    """Constroi o conjunto padrao de itens de review de fornecedor de IA."""
    return (
        ItemVendorReview(
            "transferencia_internacional",
            "Ha transferencia internacional de dados e ela atende ao Art. 33?",
            "Art. 33",
        ),
        ItemVendorReview(
            "operador_dpa",
            "Existe DPA definindo o fornecedor como operador/sub-operador?",
            "Art. 39",
        ),
        ItemVendorReview(
            "treinamento_modelo",
            "O fornecedor usa dados pessoais para treinar modelos? Ha base legal?",
            "Art. 7",
        ),
        ItemVendorReview(
            "retencao_eliminacao",
            "Ha politica clara de retencao e eliminacao dos dados enviados?",
            "Art. 16",
        ),
        ItemVendorReview(
            "seguranca_criptografia",
            "Ha criptografia em transito e repouso e controles de acesso?",
            "Art. 46",
        ),
        ItemVendorReview(
            "decisao_automatizada",
            "Ha decisao automatizada e direito de revisao garantido (Art. 20)?",
            "Art. 20",
        ),
        ItemVendorReview(
            "zero_data_retention",
            "O fornecedor oferece e comprova ZDR (Zero Data Retention)?",
            "Art. 16",
            obrigatorio=False,
        ),
        ItemVendorReview(
            "registro_operacoes",
            "O fornecedor mantem registro das operacoes de tratamento?",
            "Art. 37",
        ),
        ItemVendorReview(
            "incidentes_notificacao",
            "Ha SLA de notificacao de incidentes compativel com o Art. 48?",
            "Art. 48",
        ),
        ItemVendorReview(
            "encarregado_dpo",
            "O fornecedor possui encarregado (DPO) identificavel e contatavel?",
            "Art. 41",
        ),
    )


def checklist_vendor_padrao() -> VendorReview:
    """Cria um ``VendorReview`` com o conjunto padrao de itens.

    Returns:
        Review pronto para uso, todos os itens em ``pendente``.
    """
    return VendorReview(list(_itens_padrao()))


class VendorReview:
    """Colecao mutavel de itens de review de fornecedor de IA."""

    def __init__(self, itens: list[ItemVendorReview] | None = None) -> None:
        """Inicializa o review.

        Args:
            itens: Lista inicial de itens; vazia se None.
        """
        self._itens: list[ItemVendorReview] = list(itens) if itens is not None else []

    @property
    def itens(self) -> tuple[ItemVendorReview, ...]:
        """Tupla imutavel dos itens atuais."""
        return tuple(self._itens)

    def add(self, item: ItemVendorReview) -> None:
        """Adiciona um item ao review."""
        self._itens.append(item)

    def set_status(self, chave: str, status: StatusItem) -> bool:
        """Atualiza o status de um item pela ``chave``.

        Args:
            chave: Chave exata do item.
            status: Novo status.

        Returns:
            True se algum item foi atualizado, False caso contrario.
        """
        atualizado = False
        for i, item in enumerate(self._itens):
            if item.chave == chave:
                self._itens[i] = replace(item, status=status)
                atualizado = True
        return atualizado

    def flags(self) -> tuple[ItemVendorReview, ...]:
        """Retorna itens obrigatorios criticos ou ainda pendentes.

        Returns:
            Tupla de itens que representam risco/lacuna no review.
        """
        return tuple(
            item
            for item in self._itens
            if item.obrigatorio and item.status in ("critico", "pendente")
        )

    def score(self) -> float:
        """Fracao de itens obrigatorios aplicaveis marcados como ``ok``.

        Itens obrigatorios em ``nao_aplicavel`` saem do denominador. Retorna
        1.0 se nao houver item aplicavel.

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

    def aprovado(self) -> bool:
        """Indica se o fornecedor esta apto: sem criticos e sem pendentes obrigatorios.

        Returns:
            True se nenhum item esta ``critico`` e nenhum obrigatorio esta ``pendente``.
        """
        for item in self._itens:
            if item.status == "critico":
                return False
            if item.obrigatorio and item.status == "pendente":
                return False
        return True
