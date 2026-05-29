"""Testes do contract_analyzer (Contract AI — fase v1.2)."""

from __future__ import annotations

from legalops.contract_analyzer import (
    analisar_contrato,
    analisar_financiamento,
    scan_clausulas_abusivas,
    scan_nda,
)


def test_scan_detecta_juros_capitalizados() -> None:
    # Arrange
    texto = "O contrato preve capitalizacao mensal de juros sobre o saldo devedor."
    # Act
    achados = scan_clausulas_abusivas(texto)
    # Assert
    assert any(c.tipo == "juros_capitalizados" for c in achados)


def test_scan_juros_capitalizados_severidade_alta() -> None:
    achados = scan_clausulas_abusivas("Havera anatocismo no presente instrumento.")
    alvo = next(c for c in achados if c.tipo == "juros_capitalizados")
    assert alvo.severidade == "alta"


def test_scan_detecta_rescisao_unilateral() -> None:
    texto = "A rescisao podera ocorrer de forma unilateral pela contratada."
    achados = scan_clausulas_abusivas(texto)
    assert any(c.tipo == "rescisao_unilateral" for c in achados)


def test_scan_detecta_renuncia_direito() -> None:
    texto = "O contratante renuncia expressamente ao direito de reclamacao."
    achados = scan_clausulas_abusivas(texto)
    assert any(c.tipo == "renuncia_direito" for c in achados)


def test_multa_ate_2pct_nao_e_abusiva() -> None:
    texto = "Em caso de mora, incide multa de 2% sobre o valor da parcela."
    achados = scan_clausulas_abusivas(texto)
    assert not any(c.tipo == "multa_excessiva" for c in achados)


def test_multa_acima_2pct_e_abusiva() -> None:
    texto = "Em caso de mora, incide multa de 10% sobre o valor da parcela."
    achados = scan_clausulas_abusivas(texto)
    assert any(c.tipo == "multa_excessiva" for c in achados)


def test_foro_eleicao_em_adesao_flag() -> None:
    texto = "Trata-se de contrato de adesao. Fica eleito o foro da comarca de Sao Paulo."
    achados = scan_clausulas_abusivas(texto)
    assert any(c.tipo == "foro_eleicao_adesao" for c in achados)


def test_foro_eleicao_sem_adesao_nao_flag() -> None:
    texto = "Fica eleito o foro da comarca de Curitiba para dirimir duvidas."
    achados = scan_clausulas_abusivas(texto)
    assert not any(c.tipo == "foro_eleicao_adesao" for c in achados)


def test_scan_texto_vazio() -> None:
    assert scan_clausulas_abusivas("") == ()


def test_financiamento_extrai_spread() -> None:
    fin = analisar_financiamento("O spread bancario sera de 12,5% ao ano.")
    assert fin.spread_pct == 12.5


def test_financiamento_spread_alto_gera_alerta() -> None:
    fin = analisar_financiamento("O spread aplicado e de 45% conforme tabela.")
    assert any("Spread" in a for a in fin.alertas)


def test_financiamento_extrai_indexador() -> None:
    fin = analisar_financiamento("Taxa atrelada ao CDI mais spread.")
    assert fin.indexador == "CDI"


def test_financiamento_capitalizacao_detectada() -> None:
    fin = analisar_financiamento("Aplica-se capitalizacao mensal dos encargos.")
    assert fin.capitalizacao_mensal is True


def test_financiamento_taxa_mensal() -> None:
    fin = analisar_financiamento("Juros de 1,99% ao mes sobre o saldo.")
    assert fin.taxa_juros_mensal_pct == 1.99


def test_financiamento_iof() -> None:
    fin = analisar_financiamento("Incide IOF na liberacao do credito.")
    assert fin.iof_presente is True


def test_nda_vazio() -> None:
    assert scan_nda("") == ("NDA vazio ou ilegivel.",)


def test_nda_sem_prazo_gera_observacao() -> None:
    texto = "As informacoes confidenciais nao poderao ser divulgadas. Multa por violacao."
    obs = scan_nda(texto)
    assert any("Prazo" in o for o in obs)


def test_nda_prazo_excessivo() -> None:
    texto = (
        "As informacoes confidenciais ficam protegidas pelo prazo de 10 anos. "
        "Multa em caso de descumprimento."
    )
    obs = scan_nda(texto)
    assert any("superior a 5 anos" in o for o in obs)


def test_nda_completo_sem_observacoes() -> None:
    texto = (
        "As informacoes confidenciais sao protegidas por vigencia de 3 anos. "
        "A violacao sujeita o infrator a multa contratual."
    )
    obs = scan_nda(texto)
    assert obs == ()


def test_relatorio_nivel_alto() -> None:
    texto = (
        "Contrato de adesao. O contratante renuncia ao direito de reclamar. "
        "A rescisao sera unilateral a criterio do banco. Havera anatocismo."
    )
    rel = analisar_contrato(texto)
    assert rel.nivel == "alto"


def test_relatorio_vazio_baixo() -> None:
    rel = analisar_contrato("Contrato de prestacao de servicos padrao e equilibrado.")
    assert rel.nivel == "baixo"


def test_relatorio_texto_vazio() -> None:
    rel = analisar_contrato("")
    assert rel.score == 0 and "vazio" in rel.recomendacoes[0]


def test_relatorio_inclui_financiamento_quando_presente() -> None:
    rel = analisar_contrato("Financiamento com spread de 8% atrelado a SELIC.")
    assert rel.financiamento is not None and rel.financiamento.indexador == "SELIC"


def test_relatorio_recomendacoes_para_clausula() -> None:
    rel = analisar_contrato("Havera capitalizacao mensal de juros.")
    assert any("juros_capitalizados" in r for r in rel.recomendacoes)
