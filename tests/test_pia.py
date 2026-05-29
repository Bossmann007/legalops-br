"""Tests for pia module (RIPD, Art. 38 LGPD)."""

from __future__ import annotations

from legalops.lgpd_specifics import BaseLegal, OperacaoTratamento, TipoDado
from legalops.pia import avaliar_ripd


def _op(**kwargs: object) -> OperacaoTratamento:
    base: dict[str, object] = {
        "tipo_operacao": "coleta",
        "tipos_dados": [TipoDado.COMUM],
        "base_legal": BaseLegal.CONSENTIMENTO,
        "finalidade": "cadastro de cliente",
        "necessario": True,
    }
    base.update(kwargs)
    return OperacaoTratamento(**base)  # type: ignore[arg-type]


class TestRIPDScoring:
    def test_operacao_simples_baixo(self) -> None:
        ripd = avaliar_ripd(_op())

        assert ripd.nivel == "baixo"

    def test_operacao_simples_score_zero(self) -> None:
        ripd = avaliar_ripd(_op())

        assert ripd.score == 0

    def test_sensivel_gera_risco_alto(self) -> None:
        ripd = avaliar_ripd(_op(tipos_dados=[TipoDado.SENSIVEL]))

        assert any(r.severidade == "alto" and r.artigo == "Art. 11" for r in ripd.riscos)

    def test_crianca_gera_risco_art14(self) -> None:
        ripd = avaliar_ripd(_op(tipos_dados=[TipoDado.CRIANCA]))

        assert any(r.artigo == "Art. 14" for r in ripd.riscos)

    def test_legitimo_interesse_sensivel_critico(self) -> None:
        ripd = avaliar_ripd(
            _op(tipos_dados=[TipoDado.SENSIVEL], base_legal=BaseLegal.LEGITIMO_INTERESSE)
        )

        assert any(r.severidade == "critico" for r in ripd.riscos)

    def test_nao_necessario_gera_risco_medio(self) -> None:
        ripd = avaliar_ripd(_op(necessario=False))

        assert any(r.severidade == "medio" and r.artigo == "Art. 6 III" for r in ripd.riscos)

    def test_score_ponderado_sensivel(self) -> None:
        # SENSIVEL com base valida -> apenas 1 risco alto (peso 5).
        ripd = avaliar_ripd(_op(tipos_dados=[TipoDado.SENSIVEL]))

        assert ripd.score == 5


class TestConforme:
    def test_conforme_quando_valido_sem_critico(self) -> None:
        ripd = avaliar_ripd(_op())

        assert ripd.conforme is True

    def test_nao_conforme_quando_critico(self) -> None:
        ripd = avaliar_ripd(
            _op(tipos_dados=[TipoDado.SENSIVEL], base_legal=BaseLegal.LEGITIMO_INTERESSE)
        )

        assert ripd.conforme is False

    def test_nao_conforme_finalidade_vazia(self) -> None:
        ripd = avaliar_ripd(_op(finalidade=""))

        assert ripd.conforme is False

    def test_finalidade_vazia_gera_risco(self) -> None:
        ripd = avaliar_ripd(_op(finalidade=""))

        assert any(r.artigo == "Art. 6 I" for r in ripd.riscos)


class TestNivel:
    def test_nivel_alto_quando_risco_unico_alto(self) -> None:
        # crianca: unico risco Art.14 (alto, peso 5). Score 5 < limiar alto (6),
        # mas o nivel acompanha o pior risco isolado -> 'alto'.
        ripd = avaliar_ripd(_op(tipos_dados=[TipoDado.CRIANCA]))

        assert ripd.nivel == "alto"
        # risco listado uma unica vez (sem duplicacao do aviso).
        art14 = [r for r in ripd.riscos if r.artigo == "Art. 14"]
        assert len(art14) == 1
        assert art14[0].severidade == "alto"

    def test_nivel_critico_quando_score_alto(self) -> None:
        # sensivel(5) + legitimo-interesse-sensivel critico(8) = 13 -> critico.
        ripd = avaliar_ripd(
            _op(tipos_dados=[TipoDado.SENSIVEL], base_legal=BaseLegal.LEGITIMO_INTERESSE)
        )

        assert ripd.nivel == "critico"

    def test_operacao_nome_preservado(self) -> None:
        ripd = avaliar_ripd(_op(tipo_operacao="armazenamento"))

        assert ripd.operacao == "armazenamento"
