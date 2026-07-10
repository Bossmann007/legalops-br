from datetime import date

from legalops.prazo_oracle import (
    CAMPOS_CHAVE,
    LEGAL_PRAZO_SET,
    extractions_agree,
    is_duplicate,
    validate_cnj_tribunal,
    validate_data_publicacao,
    validate_prazo_dias,
)


def test_prazo_dias_valido():
    assert validate_prazo_dias(15) is True


def test_prazo_dias_fora_do_conjunto():
    assert validate_prazo_dias(13) is False


def test_prazo_dias_zero_ou_negativo():
    assert validate_prazo_dias(0) is False
    assert validate_prazo_dias(-5) is False


def test_conjunto_legal_contem_prazos_comuns():
    for d in (5, 10, 15, 30):
        assert d in LEGAL_PRAZO_SET


def test_data_publicacao_hoje_ok():
    hoje = date(2026, 7, 9)
    assert validate_data_publicacao(date(2026, 7, 9), hoje=hoje) is True


def test_data_publicacao_futura_rejeitada():
    hoje = date(2026, 7, 9)
    assert validate_data_publicacao(date(2026, 7, 10), hoje=hoje) is False


def test_data_publicacao_antiga_demais_rejeitada():
    hoje = date(2026, 7, 9)
    # > 365 dias atrás: implausível para uma intimação sendo processada agora
    assert validate_data_publicacao(date(2025, 1, 1), hoje=hoje) is False


def test_data_publicacao_recente_ok():
    hoje = date(2026, 7, 9)
    assert validate_data_publicacao(date(2026, 6, 1), hoje=hoje) is True


def test_cnj_tjpr_consistente():
    # segmento 8 (estadual), TR 16 (PR)
    assert validate_cnj_tribunal("0001234-56.2026.8.16.0001", "TJPR") is True


def test_cnj_tjpr_inconsistente_com_trf4():
    # CNJ é estadual PR mas extração diz TRF4 → conflito
    assert validate_cnj_tribunal("0001234-56.2026.8.16.0001", "TRF4") is False


def test_cnj_trf4_consistente():
    # segmento 4 (federal), TR 04 (4a região)
    assert validate_cnj_tribunal("0007654-32.2026.4.04.7000", "TRF4") is True


def test_tribunal_fora_do_mapa_inconclusivo():
    assert validate_cnj_tribunal("0001234-56.2026.8.26.0001", "TJXX") is None


def test_cnj_malformado_inconclusivo():
    assert validate_cnj_tribunal("nao-e-um-cnj", "TJPR") is None
    assert validate_cnj_tribunal("", "TJPR") is None


def test_dedup_ref_e_ato_iguais_e_duplicata():
    ledger = [{"ref": "PROC-1", "ato": "contestacao", "status": "aberto"}]
    assert is_duplicate("PROC-1", "contestacao", ledger) is True


def test_dedup_mesmo_ref_ato_diferente_nao_e_duplicata():
    ledger = [{"ref": "PROC-1", "ato": "contestacao", "status": "aberto"}]
    assert is_duplicate("PROC-1", "replica", ledger) is False


def test_dedup_ref_novo_nao_e_duplicata():
    ledger = [{"ref": "PROC-1", "ato": "contestacao", "status": "aberto"}]
    assert is_duplicate("PROC-2", "contestacao", ledger) is False


def test_dedup_ledger_vazio():
    assert is_duplicate("PROC-1", "contestacao", []) is False


def test_dedup_case_insensitive_no_ato():
    ledger = [{"ref": "PROC-1", "ato": "Contestacao", "status": "aberto"}]
    assert is_duplicate("PROC-1", "contestacao", ledger) is True


def _extr(**kw):
    base = {
        "data_publicacao": "2026-07-01",
        "prazo_dias": 15,
        "parte": "particular",
        "tribunal": "TJPR",
        "via_dje": True,
        "confianca": 0.9,
    }
    base.update(kw)
    return base


def test_extractions_iguais_concordam():
    assert extractions_agree(_extr(), _extr()) is True


def test_divergencia_em_prazo_dias_nao_concorda():
    assert extractions_agree(_extr(prazo_dias=15), _extr(prazo_dias=30)) is False


def test_divergencia_em_via_dje_nao_concorda():
    assert extractions_agree(_extr(via_dje=True), _extr(via_dje=False)) is False


def test_confianca_diferente_ainda_concorda():
    # confiança não é campo-chave; diferença nela não quebra concordância
    assert extractions_agree(_extr(confianca=0.5), _extr(confianca=0.99)) is True


def test_campos_chave_nao_incluem_confianca():
    assert "confianca" not in CAMPOS_CHAVE
