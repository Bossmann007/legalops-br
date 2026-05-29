"""Tests for legalops.doc_extractor — extracao de campos de documentos."""

from __future__ import annotations

from datetime import date

from legalops.doc_extractor import (
    extract_contrato_honorarios,
    extract_procuracao,
)

PROCURACAO_COMPLETA = (
    "PROCURACAO\n"
    "Outorgante: ACME COMERCIO LTDA;\n"
    "Outorgado: Dr. Fulano de Tal, OAB/PR 12345;\n"
    "concede poderes ad judicia et extra para o foro em geral, "
    "perante a Comarca de Curitiba.\n"
    "Curitiba, 10/03/2026.\n"
)

CONTRATO_COMPLETO = (
    "CONTRATO DE HONORARIOS\n"
    "Contratante: ACME COMERCIO LTDA;\n"
    "Contratado: Banca Fulano Advogados, OAB/PR 99999;\n"
    "Objeto: patrocinio de acao trabalhista;\n"
    "Honorarios: R$ 5.000,00 a vista, mais exito de 20%.\n"
    "Foro: Comarca de Sao Jose dos Pinhais.\n"
)


def test_procuracao_extrai_outorgante() -> None:
    # Arrange / Act
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    # Assert
    assert campos.outorgante == "ACME COMERCIO LTDA"


def test_procuracao_extrai_outorgado() -> None:
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    assert campos.outorgado == "Dr. Fulano de Tal"


def test_procuracao_extrai_oab_com_uf() -> None:
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    assert campos.oab == "PR 12345"


def test_procuracao_detecta_ad_judicia_et_extra() -> None:
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    assert campos.poderes == "ad_judicia_et_extra"


def test_procuracao_detecta_ad_judicia_simples() -> None:
    campos = extract_procuracao("outorga poderes ad judicia para o foro.")

    assert campos.poderes == "ad_judicia"


def test_procuracao_detecta_poderes_especiais() -> None:
    campos = extract_procuracao("com poderes especiais para transigir e alienar.")

    assert campos.poderes == "especiais"


def test_procuracao_extrai_comarca() -> None:
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    assert campos.comarca == "Curitiba"


def test_procuracao_extrai_data() -> None:
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    assert campos.data == date(2026, 3, 10)


def test_procuracao_confianca_total() -> None:
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    assert campos.confianca == 1.0


def test_procuracao_sem_campos_ausentes_quando_completa() -> None:
    campos = extract_procuracao(PROCURACAO_COMPLETA)

    assert campos.campos_ausentes == ()


def test_procuracao_campos_ausentes_listados() -> None:
    campos = extract_procuracao("Outorgante: ACME LTDA")

    assert "comarca" in campos.campos_ausentes


def test_procuracao_vazia_confianca_zero() -> None:
    campos = extract_procuracao("")

    assert campos.confianca == 0.0


def test_procuracao_vazia_todos_ausentes() -> None:
    campos = extract_procuracao("   ")

    assert len(campos.campos_ausentes) == 5


def test_procuracao_garbage_poderes_desconhecido() -> None:
    campos = extract_procuracao("xyzzy lorem ipsum 123")

    assert campos.poderes == "desconhecido"


def test_procuracao_oab_sem_uf() -> None:
    campos = extract_procuracao("Outorgado: Dr. Beltrano, OAB n. 54321.")

    assert campos.oab == "54321"


def test_contrato_extrai_contratante() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.contratante == "ACME COMERCIO LTDA"


def test_contrato_extrai_contratado() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.contratado == "Banca Fulano Advogados"


def test_contrato_extrai_objeto() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.objeto == "patrocinio de acao trabalhista"


def test_contrato_extrai_valor_reais() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.valor == 5000.00


def test_contrato_extrai_percentual_exito() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.percentual == 20


def test_contrato_forma_pagamento_misto() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.forma_pagamento == "misto"


def test_contrato_forma_pagamento_a_vista() -> None:
    campos = extract_contrato_honorarios("Pagamento a vista de R$ 1.000,00.")

    assert campos.forma_pagamento == "a_vista"


def test_contrato_forma_pagamento_parcelado() -> None:
    campos = extract_contrato_honorarios("Pagamento parcelado em 3 parcelas.")

    assert campos.forma_pagamento == "parcelado"


def test_contrato_forma_pagamento_exito() -> None:
    campos = extract_contrato_honorarios("Honorarios de exito de 30%.")

    assert campos.forma_pagamento == "exito"


def test_contrato_forma_pagamento_desconhecido() -> None:
    campos = extract_contrato_honorarios("texto sem forma de pagamento.")

    assert campos.forma_pagamento == "desconhecido"


def test_contrato_extrai_foro_eleicao() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.foro_eleicao == "Sao Jose dos Pinhais"


def test_contrato_confianca_total() -> None:
    campos = extract_contrato_honorarios(CONTRATO_COMPLETO)

    assert campos.confianca == 1.0


def test_contrato_campos_ausentes_listados() -> None:
    campos = extract_contrato_honorarios("Contratante: ACME LTDA")

    assert "valor" in campos.campos_ausentes


def test_contrato_vazio_confianca_zero() -> None:
    campos = extract_contrato_honorarios("")

    assert campos.confianca == 0.0


def test_contrato_vazio_todos_ausentes() -> None:
    campos = extract_contrato_honorarios("")

    assert len(campos.campos_ausentes) == 6


def test_contrato_sem_valor_retorna_none() -> None:
    campos = extract_contrato_honorarios("Objeto: defesa. Foro: Comarca de Curitiba.")

    assert campos.valor is None


def test_contrato_sem_percentual_retorna_none() -> None:
    campos = extract_contrato_honorarios("Honorarios de R$ 1.000,00 a vista.")

    assert campos.percentual is None
