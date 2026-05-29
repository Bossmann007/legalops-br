"""Tests for dpa_templates module (Art. 39 LGPD)."""

from __future__ import annotations

from legalops.dpa_templates import DPAParams, clausulas_obrigatorias, render_dpa


def _params(**kwargs: object) -> DPAParams:
    base: dict[str, object] = {
        "controlador": "Escritorio X",
        "operador": "Fornecedor Y",
        "objeto": "hospedagem de dados",
        "finalidade": "prestacao de servico SaaS",
        "categorias_dados": ("nome", "email"),
        "prazo_retencao": "vigencia do contrato",
        "suboperadores_permitidos": False,
        "transferencia_internacional": False,
    }
    base.update(kwargs)
    return DPAParams(**base)  # type: ignore[arg-type]


class TestRenderDPA:
    def test_titulo_presente(self) -> None:
        texto = render_dpa(_params())

        assert "ACORDO DE TRATAMENTO DE DADOS (OPERADOR)" in texto

    def test_partes_renderizadas(self) -> None:
        texto = render_dpa(_params())

        assert "Escritorio X" in texto and "Fornecedor Y" in texto

    def test_categorias_renderizadas(self) -> None:
        texto = render_dpa(_params())

        assert "nome, email" in texto

    def test_suboperadores_vedado_por_default(self) -> None:
        texto = render_dpa(_params(suboperadores_permitidos=False))

        assert "vedada ao OPERADOR a subcontratacao" in texto

    def test_suboperadores_permitido(self) -> None:
        texto = render_dpa(_params(suboperadores_permitidos=True))

        assert "podera subcontratar suboperadores" in texto

    def test_transferencia_internacional_ativa(self) -> None:
        texto = render_dpa(_params(transferencia_internacional=True))

        assert "transferencia internacional de dados observara" in texto

    def test_transferencia_internacional_inativa(self) -> None:
        texto = render_dpa(_params(transferencia_internacional=False))

        assert "nao realizara transferencia internacional" in texto

    def test_placeholder_campo_vazio(self) -> None:
        texto = render_dpa(_params(controlador=""))

        assert "[A PREENCHER: controlador]" in texto

    def test_placeholder_categorias_vazias(self) -> None:
        texto = render_dpa(_params(categorias_dados=()))

        assert "[A PREENCHER: categorias_dados]" in texto

    def test_nunca_levanta_excecao(self) -> None:
        texto = render_dpa(
            _params(
                controlador="",
                operador="",
                objeto="",
                finalidade="",
                categorias_dados=("", "  "),
                prazo_retencao="",
            )
        )

        assert "ACORDO DE TRATAMENTO DE DADOS" in texto


class TestClausulasObrigatorias:
    def test_retorna_oito_clausulas(self) -> None:
        assert len(clausulas_obrigatorias()) == 8

    def test_inclui_art39(self) -> None:
        assert any("Art. 39" in c for c in clausulas_obrigatorias())
