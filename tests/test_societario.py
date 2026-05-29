"""Tests para societario — estruturas sinteticas, sem dados reais."""

from __future__ import annotations

from legalops.societario import (
    EstruturaSocietaria,
    Socio,
    detect_tipo_sociedade,
    quorum_deliberacao,
    validar_participacoes,
)

# CNPJ valido sintetico (digito verificador correto).
CNPJ_VALIDO = "11.222.333/0001-81"
CNPJ_INVALIDO = "11.222.333/0001-99"


class TestDetectTipoSociedade:
    def test_ltda(self) -> None:
        assert detect_tipo_sociedade("Empresa Exemplo Ltda") == "ltda"

    def test_sociedade_limitada(self) -> None:
        assert detect_tipo_sociedade("constituida como Sociedade Limitada") == "ltda"

    def test_sa_fechada(self) -> None:
        assert detect_tipo_sociedade("Exemplo S.A.") == "sa_fechada"

    def test_sa_barra(self) -> None:
        assert detect_tipo_sociedade("Exemplo S/A") == "sa_fechada"

    def test_sa_aberta(self) -> None:
        assert detect_tipo_sociedade("Companhia Aberta listada na B3") == "sa_aberta"

    def test_eireli(self) -> None:
        assert detect_tipo_sociedade("constituida sob a forma de EIRELI") == "eireli"

    def test_mei(self) -> None:
        assert detect_tipo_sociedade("Microempreendedor Individual") == "mei"

    def test_slu_antes_de_ltda(self) -> None:
        assert detect_tipo_sociedade("Sociedade Limitada Unipessoal") == "slu"

    def test_desconhecido(self) -> None:
        assert detect_tipo_sociedade("texto generico sem forma") == "desconhecido"

    def test_vazio(self) -> None:
        assert detect_tipo_sociedade("") == "desconhecido"


class TestQuorumDeliberacao:
    def _estrutura(self, tipo: str = "ltda") -> EstruturaSocietaria:
        return EstruturaSocietaria(tipo=tipo, cnpj=None, socios=(), capital_social=None)  # type: ignore[arg-type]

    def test_alteracao_contrato_ltda(self) -> None:
        assert quorum_deliberacao(self._estrutura("ltda"), "alteracao_contrato") == 75.0

    def test_dissolucao_ltda(self) -> None:
        assert quorum_deliberacao(self._estrutura("ltda"), "dissolucao") == 75.0

    def test_operacoes_ordinarias_ltda(self) -> None:
        assert quorum_deliberacao(self._estrutura("ltda"), "operacoes_ordinarias") == 50.0

    def test_exclusao_socio_ltda(self) -> None:
        assert quorum_deliberacao(self._estrutura("ltda"), "exclusao_socio") == 50.0

    def test_sa_sempre_50(self) -> None:
        assert quorum_deliberacao(self._estrutura("sa_aberta"), "alteracao_contrato") == 50.0


class TestValidarParticipacoes:
    def test_estrutura_valida(self) -> None:
        est = EstruturaSocietaria(
            tipo="ltda",
            cnpj=CNPJ_VALIDO,
            socios=(Socio("Socio A", 60.0), Socio("Socio B", 40.0)),
            capital_social=100000.0,
        )
        assert validar_participacoes(est) == ()

    def test_soma_diferente_de_100(self) -> None:
        est = EstruturaSocietaria(
            tipo="ltda",
            cnpj=None,
            socios=(Socio("Socio A", 60.0), Socio("Socio B", 30.0)),
            capital_social=None,
        )
        problemas = validar_participacoes(est)
        assert any("Soma" in p for p in problemas)

    def test_cnpj_invalido(self) -> None:
        est = EstruturaSocietaria(
            tipo="ltda",
            cnpj=CNPJ_INVALIDO,
            socios=(Socio("Socio A", 100.0),),
            capital_social=None,
        )
        problemas = validar_participacoes(est)
        assert any("CNPJ" in p for p in problemas)

    def test_mei_com_dois_socios(self) -> None:
        est = EstruturaSocietaria(
            tipo="mei",
            cnpj=None,
            socios=(Socio("A", 50.0), Socio("B", 50.0)),
            capital_social=None,
        )
        problemas = validar_participacoes(est)
        assert any("mei" in p for p in problemas)

    def test_sem_socios(self) -> None:
        est = EstruturaSocietaria(tipo="ltda", cnpj=None, socios=(), capital_social=None)
        problemas = validar_participacoes(est)
        assert any("sem socios" in p.lower() for p in problemas)

    def test_participacao_fora_intervalo(self) -> None:
        est = EstruturaSocietaria(
            tipo="ltda",
            cnpj=None,
            socios=(Socio("A", 120.0),),
            capital_social=None,
        )
        problemas = validar_participacoes(est)
        assert any("intervalo" in p for p in problemas)
