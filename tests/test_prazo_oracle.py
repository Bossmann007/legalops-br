from legalops.prazo_oracle import LEGAL_PRAZO_SET, validate_prazo_dias


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
