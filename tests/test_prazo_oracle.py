from datetime import date

from legalops.prazo_oracle import (
    LEGAL_PRAZO_SET,
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
