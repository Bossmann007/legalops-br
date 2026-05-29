"""Tests para data_room — docs sinteticos, sem dados reais."""

from __future__ import annotations

from legalops.data_room import (
    DataRoomDoc,
    DataRoomIndex,
    classify_document,
)


class TestClassifyDocument:
    def test_contrato_social(self) -> None:
        assert classify_document("Contrato Social da empresa") == "contrato_social"

    def test_balanco(self) -> None:
        assert classify_document("Balanco Patrimonial 2025") == "balanco"

    def test_dre(self) -> None:
        assert classify_document("Demonstracao do Resultado do Exercicio") == "balanco"

    def test_certidao(self) -> None:
        assert classify_document("Certidao Negativa de Debitos") == "certidao"

    def test_processo_judicial_por_cnj(self) -> None:
        assert classify_document("0001234-56.2026.8.16.0001") == "processo_judicial"

    def test_licenca_ambiental(self) -> None:
        assert classify_document("Licenca Ambiental de Operacao") == "licenca_ambiental"

    def test_folha_pagamento(self) -> None:
        assert classify_document("Folha de Pagamento mensal") == "folha_pagamento"

    def test_contrato_comercial(self) -> None:
        assert classify_document("Contrato de Prestacao de servicos") == "contrato_comercial"

    def test_outros(self) -> None:
        assert classify_document("memorando interno qualquer") == "outros"

    def test_vazio(self) -> None:
        assert classify_document("") == "outros"


class TestDataRoomIndex:
    def test_add_e_docs(self) -> None:
        idx = DataRoomIndex()
        idx.add(DataRoomDoc("a.pdf", "balanco"))
        assert len(idx.docs) == 1

    def test_por_tipo(self) -> None:
        idx = DataRoomIndex(
            [DataRoomDoc("a", "balanco"), DataRoomDoc("b", "balanco"), DataRoomDoc("c", "certidao")]
        )
        assert idx.por_tipo() == {"balanco": 2, "certidao": 1}

    def test_auditar_completude_faltando(self) -> None:
        idx = DataRoomIndex([DataRoomDoc("a", "balanco")])
        faltantes = idx.auditar_completude(("balanco", "certidao", "contrato_social"))
        assert faltantes == ("certidao", "contrato_social")

    def test_auditar_completude_completo(self) -> None:
        idx = DataRoomIndex([DataRoomDoc("a", "balanco"), DataRoomDoc("b", "certidao")])
        assert idx.auditar_completude(("balanco", "certidao")) == ()

    def test_auditar_sem_duplicatas(self) -> None:
        idx = DataRoomIndex([])
        assert idx.auditar_completude(("balanco", "balanco")) == ("balanco",)
