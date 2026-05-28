"""Tests tribunal_detector — corpus sintetico."""

from __future__ import annotations

from legalops.tribunal_detector import detect_tribunal


class TestDomain:
    def test_tjsp_via_sender(self) -> None:
        assert detect_tribunal("body irrelevante", sender="naoresponda@tjsp.jus.br") == "tjsp"

    def test_tjpr_via_sender(self) -> None:
        assert detect_tribunal("body", sender="projudi@tjpr.jus.br") == "tjpr"

    def test_tjsp_subdomain(self) -> None:
        assert detect_tribunal("", sender="esaj@web.tjsp.jus.br") == "tjsp"

    def test_sender_case_insensitive(self) -> None:
        assert detect_tribunal("", sender="X@TJSP.JUS.BR") == "tjsp"


class TestHeader:
    def test_esaj_header(self) -> None:
        assert detect_tribunal("Sistema e-SAJ\nProcesso ...", sender="") == "tjsp"

    def test_pje_sp(self) -> None:
        assert detect_tribunal("Notificacao PJe-SP", sender="") == "tjsp"

    def test_projudi_header(self) -> None:
        assert detect_tribunal("Encaminhado pelo Projudi", sender="") == "tjpr"

    def test_tjsp_full_name(self) -> None:
        assert detect_tribunal("Tribunal de Justica de Sao Paulo", sender="") == "tjsp"

    def test_tjpr_full_name(self) -> None:
        assert detect_tribunal("Tribunal de Justiça do Paraná", sender="") == "tjpr"


class TestPriority:
    def test_domain_wins_over_header(self) -> None:
        # sender TJSP mesmo com header Projudi confuso
        assert detect_tribunal("Projudi", sender="x@tjsp.jus.br") == "tjsp"


class TestTJSC:
    def test_tjsc_via_sender(self) -> None:
        assert detect_tribunal("", sender="eproc@tjsc.jus.br") == "tjsc"

    def test_tjsc_via_eproc_header(self) -> None:
        assert detect_tribunal("Sistema e-Proc TJSC", sender="") == "tjsc"

    def test_tjsc_full_name(self) -> None:
        assert detect_tribunal("Tribunal de Justica de Santa Catarina", sender="") == "tjsc"


class TestTJRJ:
    def test_tjrj_via_sender(self) -> None:
        assert detect_tribunal("", sender="pje@tjrj.jus.br") == "tjrj"

    def test_tjrj_pje_header(self) -> None:
        assert detect_tribunal("Notificacao PJe-RJ", sender="") == "tjrj"

    def test_tjrj_full_name(self) -> None:
        txt = "Tribunal de Justica do Estado do Rio de Janeiro"
        assert detect_tribunal(txt, sender="") == "tjrj"


class TestUnknown:
    def test_empty(self) -> None:
        assert detect_tribunal("", sender="") == "unknown"

    def test_unrelated(self) -> None:
        assert detect_tribunal("Random newsletter", sender="news@foo.com") == "unknown"

    def test_other_tribunal(self) -> None:
        assert detect_tribunal("Sistema TRF4", sender="x@trf4.jus.br") == "unknown"
