from datetime import date

from legalops.prazo_oracle import (
    LEGAL_PRAZO_SET,
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
