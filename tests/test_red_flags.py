"""Tests para red_flags — contratos sinteticos, sem dados reais."""

from __future__ import annotations

from legalops.red_flags import RedFlag, scan_acquisition_contract


def _tipos(flags: tuple[RedFlag, ...]) -> set[str]:
    return {f.tipo for f in flags}


class TestPresencas:
    def test_change_of_control(self) -> None:
        flags = scan_acquisition_contract("This agreement has a change of control clause.")
        assert "change_of_control" in _tipos(flags)

    def test_mac_presente(self) -> None:
        flags = scan_acquisition_contract("subject to a Material Adverse Change provision")
        assert "mac" in _tipos(flags)

    def test_indemnification_cap(self) -> None:
        flags = scan_acquisition_contract("indemnification subject to a cap of R$ 1.000.000")
        assert "indemnification_cap" in _tipos(flags)

    def test_rw_survival(self) -> None:
        flags = scan_acquisition_contract(
            "survival period of the representations and warranties is 24 months"
        )
        assert "rw_survival" in _tipos(flags)

    def test_non_compete(self) -> None:
        flags = scan_acquisition_contract("the seller agrees to a non-compete for 5 years")
        assert "non_compete" in _tipos(flags)

    def test_earn_out(self) -> None:
        flags = scan_acquisition_contract("purchase price includes an earn-out component")
        assert "earn_out" in _tipos(flags)

    def test_trecho_nao_vazio_para_presenca(self) -> None:
        flags = scan_acquisition_contract("change of control event triggers acceleration")
        coc = next(f for f in flags if f.tipo == "change_of_control")
        assert coc.trecho != ""


class TestAusencias:
    def test_mac_ausente(self) -> None:
        flags = scan_acquisition_contract("a plain contract without that protection")
        assert "mac_ausente" in _tipos(flags)

    def test_sem_cap_indenizacao(self) -> None:
        flags = scan_acquisition_contract("a plain contract without limits")
        assert "sem_cap_indenizacao" in _tipos(flags)

    def test_sem_cap_severidade_alta(self) -> None:
        flags = scan_acquisition_contract("plain text")
        cap = next(f for f in flags if f.tipo == "sem_cap_indenizacao")
        assert cap.severidade == "alta"

    def test_ausencia_tem_trecho_vazio(self) -> None:
        flags = scan_acquisition_contract("plain text")
        mac = next(f for f in flags if f.tipo == "mac_ausente")
        assert mac.trecho == ""

    def test_texto_vazio_so_ausencias(self) -> None:
        flags = scan_acquisition_contract("")
        assert _tipos(flags) == {"mac_ausente", "sem_cap_indenizacao"}

    def test_mac_presente_nao_gera_ausente(self) -> None:
        flags = scan_acquisition_contract("Material Adverse Change defined herein")
        assert "mac_ausente" not in _tipos(flags)

    def test_cap_presente_nao_gera_sem_cap(self) -> None:
        flags = scan_acquisition_contract("indemnification cap of R$ 500.000")
        assert "sem_cap_indenizacao" not in _tipos(flags)
