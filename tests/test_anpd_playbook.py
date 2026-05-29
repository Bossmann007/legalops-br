"""Tests para anpd_playbook — incidente Art. 48 (dados sinteticos)."""

from __future__ import annotations

from datetime import date

from legalops.anpd_playbook import (
    Incidente,
    avaliar_severidade,
    conteudo_minimo_comunicacao,
    gerar_plano,
)
from legalops.lgpd_specifics import TipoDado


def _inc(
    *,
    dados: tuple[TipoDado, ...] = (TipoDado.COMUM,),
    num: int = 10,
    vazamento: bool = False,
    descoberta: date = date(2026, 6, 1),
) -> Incidente:
    return Incidente(
        incidente_id="INC-001",
        descricao="Acesso indevido a tabela X.",
        data_descoberta=descoberta,
        dados_afetados=dados,
        num_titulares=num,
        vazamento_confirmado=vazamento,
    )


class TestAvaliarSeveridade:
    def test_comum_baixo_volume_e_baixa(self) -> None:
        assert avaliar_severidade(_inc()) == "baixa"

    def test_dados_sensiveis_elevam(self) -> None:
        assert avaliar_severidade(_inc(dados=(TipoDado.SENSIVEL,))) == "media"

    def test_dados_crianca_elevam(self) -> None:
        assert avaliar_severidade(_inc(dados=(TipoDado.CRIANCA,))) == "media"

    def test_volume_medio_eleva_um_nivel(self) -> None:
        assert avaliar_severidade(_inc(num=150)) == "media"

    def test_volume_alto_eleva_dois_niveis(self) -> None:
        assert avaliar_severidade(_inc(num=5000)) == "alta"

    def test_vazamento_confirmado_eleva(self) -> None:
        assert avaliar_severidade(_inc(vazamento=True)) == "media"

    def test_acumulo_chega_a_critica(self) -> None:
        sev = avaliar_severidade(_inc(dados=(TipoDado.SENSIVEL,), num=5000, vazamento=True))
        assert sev == "critica"


class TestGerarPlano:
    def test_baixa_nao_comunica_anpd(self) -> None:
        plano = gerar_plano(_inc(), hoje=date(2026, 6, 1))
        assert plano.comunicar_anpd is False

    def test_media_comunica_anpd(self) -> None:
        plano = gerar_plano(_inc(dados=(TipoDado.SENSIVEL,)), hoje=date(2026, 6, 1))
        assert plano.comunicar_anpd is True

    def test_media_nao_comunica_titulares(self) -> None:
        plano = gerar_plano(_inc(dados=(TipoDado.SENSIVEL,)), hoje=date(2026, 6, 1))
        assert plano.comunicar_titulares is False

    def test_alta_comunica_titulares(self) -> None:
        plano = gerar_plano(_inc(num=5000), hoje=date(2026, 6, 1))
        assert plano.comunicar_titulares is True

    def test_prazo_pula_fim_de_semana(self) -> None:
        # Sexta 2026-06-05 + 2 dias uteis -> terca 2026-06-09.
        plano = gerar_plano(
            _inc(dados=(TipoDado.SENSIVEL,), descoberta=date(2026, 6, 5)),
            hoje=date(2026, 6, 5),
        )
        assert plano.prazo_anpd == date(2026, 6, 9)

    def test_dias_restantes_calculado(self) -> None:
        plano = gerar_plano(
            _inc(dados=(TipoDado.SENSIVEL,), descoberta=date(2026, 6, 1)),
            hoje=date(2026, 6, 1),
        )
        assert plano.dias_restantes == 2

    def test_sem_comunicacao_prazo_none(self) -> None:
        plano = gerar_plano(_inc(), hoje=date(2026, 6, 1))
        assert plano.prazo_anpd is None

    def test_passos_nao_vazio(self) -> None:
        plano = gerar_plano(_inc(num=5000), hoje=date(2026, 6, 1))
        assert len(plano.passos) > 0

    def test_passos_incluem_anpd_quando_comunica(self) -> None:
        plano = gerar_plano(_inc(dados=(TipoDado.SENSIVEL,)), hoje=date(2026, 6, 1))
        assert any("ANPD" in p for p in plano.passos)

    def test_hoje_default_nao_falha(self) -> None:
        plano = gerar_plano(_inc())
        assert plano.severidade == "baixa"


class TestConteudoMinimo:
    def test_nao_vazio(self) -> None:
        assert len(conteudo_minimo_comunicacao()) > 0

    def test_referencia_art_48(self) -> None:
        assert all("Art. 48" in c for c in conteudo_minimo_comunicacao())
