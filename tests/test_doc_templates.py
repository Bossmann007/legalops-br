"""Tests for legalops.doc_templates — renderizacao de documentos."""

from __future__ import annotations

from datetime import date

from legalops.doc_extractor import ContratoHonorariosCampos, ProcuracaoCampos
from legalops.doc_templates import (
    render_contrato_honorarios,
    render_procuracao,
)


def _procuracao_completa() -> ProcuracaoCampos:
    return ProcuracaoCampos(
        outorgante="ACME LTDA",
        outorgado="Dr. Fulano",
        oab="PR 12345",
        poderes="ad_judicia_et_extra",
        comarca="Curitiba",
        data=date(2026, 3, 10),
    )


def _contrato_completo() -> ContratoHonorariosCampos:
    return ContratoHonorariosCampos(
        contratante="ACME LTDA",
        contratado="Banca Fulano",
        objeto="acao trabalhista",
        valor=5000.0,
        percentual=20,
        forma_pagamento="misto",
        foro_eleicao="Curitiba",
    )


def test_procuracao_render_inclui_titulo() -> None:
    texto = render_procuracao(_procuracao_completa())

    assert texto.startswith("PROCURACAO")


def test_procuracao_render_inclui_outorgante() -> None:
    texto = render_procuracao(_procuracao_completa())

    assert "ACME LTDA" in texto


def test_procuracao_render_inclui_oab() -> None:
    texto = render_procuracao(_procuracao_completa())

    assert "PR 12345" in texto


def test_procuracao_render_inclui_data_formatada() -> None:
    texto = render_procuracao(_procuracao_completa())

    assert "10/03/2026" in texto


def test_procuracao_render_poderes_et_extra() -> None:
    texto = render_procuracao(_procuracao_completa())

    assert "ad judicia et extra" in texto


def test_procuracao_render_placeholder_outorgante_ausente() -> None:
    texto = render_procuracao(ProcuracaoCampos())

    assert "[A PREENCHER: outorgante]" in texto


def test_procuracao_render_placeholder_data_ausente() -> None:
    texto = render_procuracao(ProcuracaoCampos(outorgante="X"))

    assert "[A PREENCHER: data]" in texto


def test_procuracao_render_sem_oab_omite_linha() -> None:
    campos = ProcuracaoCampos(outorgante="X", outorgado="Y", oab=None)

    texto = render_procuracao(campos)

    assert "OAB sob" not in texto


def test_procuracao_render_poderes_desconhecido_placeholder() -> None:
    texto = render_procuracao(ProcuracaoCampos(poderes="desconhecido"))

    assert "[A PREENCHER: poderes]" in texto


def test_procuracao_render_nao_lanca_em_vazio() -> None:
    texto = render_procuracao(ProcuracaoCampos())

    assert isinstance(texto, str)


def test_contrato_render_inclui_titulo() -> None:
    texto = render_contrato_honorarios(_contrato_completo())

    assert "PRESTACAO DE SERVICOS" in texto


def test_contrato_render_inclui_contratante() -> None:
    texto = render_contrato_honorarios(_contrato_completo())

    assert "ACME LTDA" in texto


def test_contrato_render_inclui_valor_formatado_br() -> None:
    texto = render_contrato_honorarios(_contrato_completo())

    assert "R$ 5.000,00" in texto


def test_contrato_render_inclui_percentual_exito() -> None:
    texto = render_contrato_honorarios(_contrato_completo())

    assert "20%" in texto


def test_contrato_render_inclui_foro() -> None:
    texto = render_contrato_honorarios(_contrato_completo())

    assert "Curitiba" in texto


def test_contrato_render_placeholder_valor_ausente() -> None:
    campos = ContratoHonorariosCampos(contratante="X", valor=None)

    texto = render_contrato_honorarios(campos)

    assert "[A PREENCHER: valor]" in texto


def test_contrato_render_sem_percentual_omite_exito() -> None:
    campos = ContratoHonorariosCampos(percentual=None)

    texto = render_contrato_honorarios(campos)

    assert "exito de" not in texto


def test_contrato_render_placeholder_objeto_ausente() -> None:
    texto = render_contrato_honorarios(ContratoHonorariosCampos())

    assert "[A PREENCHER: objeto]" in texto


def test_contrato_render_forma_desconhecida_placeholder() -> None:
    texto = render_contrato_honorarios(ContratoHonorariosCampos())

    assert "[A PREENCHER: forma_pagamento]" in texto


def test_contrato_render_nao_lanca_em_vazio() -> None:
    texto = render_contrato_honorarios(ContratoHonorariosCampos())

    assert isinstance(texto, str)
