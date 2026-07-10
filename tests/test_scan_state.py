from datetime import date

from legalops.scan_state import ScanState, describe_state, load_scan_state, save_scan_state


def test_nunca_varreu():
    d = describe_state(None, hoje=date(2026, 7, 10))
    assert d["estado"] == "nunca"
    assert "/varrer" in d["comando_sugerido"]


def test_varreu_hoje_ok():
    s = ScanState(ultima_varredura="2026-07-10T09:15:00", resultado="ok", n_encontrados=3)
    d = describe_state(s, hoje=date(2026, 7, 10))
    assert d["estado"] == "ok"


def test_varreu_hoje_vazio():
    s = ScanState(ultima_varredura="2026-07-10T09:15:00", resultado="vazio", n_encontrados=0)
    d = describe_state(s, hoje=date(2026, 7, 10))
    assert d["estado"] == "vazio"


def test_varreu_hoje_falha():
    s = ScanState(ultima_varredura="2026-07-10T09:15:00", resultado="falha", n_encontrados=0)
    d = describe_state(s, hoje=date(2026, 7, 10))
    assert d["estado"] == "falha"
    assert "cole" in d["mensagem"].lower() or "/intimacao" in d["comando_sugerido"]


def test_varreu_ontem_trata_como_nunca_hoje():
    # varredura de ontem não conta como "olhei hoje"
    s = ScanState(ultima_varredura="2026-07-09T18:00:00", resultado="ok", n_encontrados=2)
    d = describe_state(s, hoje=date(2026, 7, 10))
    assert d["estado"] == "nunca"


def test_save_load_roundtrip(tmp_path):
    p = tmp_path / "scan-state.json"
    s = ScanState(
        ultima_varredura="2026-07-10T09:15:00",
        resultado="ok",
        n_encontrados=3,
        n_processados=2,
        n_revisao=1,
    )
    save_scan_state(s, p)
    got = load_scan_state(p)
    assert got == s


def test_load_ausente_retorna_none(tmp_path):
    assert load_scan_state(tmp_path / "nao-existe.json") is None
