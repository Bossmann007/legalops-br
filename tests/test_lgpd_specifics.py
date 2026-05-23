"""Tests for lgpd_specifics module."""

from __future__ import annotations

from legalops.lgpd_specifics import (
    DIREITOS_TITULAR,
    PRAZO_INCIDENTE_ANPD_DIAS,
    PRAZO_RESPOSTA_TITULAR_DIAS,
    BaseLegal,
    DireitoTitular,
    OperacaoTratamento,
    TipoDado,
    validar_operacao,
)


class TestEnumCoverage:
    def test_base_legal_has_all_ten_art7_bases(self) -> None:
        # Art. 7 LGPD lista 10 bases legais (I a X)
        assert len(BaseLegal) == 10

    def test_base_legal_contains_expected_members(self) -> None:
        expected = {
            "consentimento",
            "obrigacao_legal",
            "politica_publica",
            "pesquisa",
            "execucao_contrato",
            "exercicio_direito",
            "protecao_vida",
            "tutela_saude",
            "legitimo_interesse",
            "protecao_credito",
        }
        actual = {b.value for b in BaseLegal}
        assert actual == expected

    def test_tipo_dado_has_three_categories(self) -> None:
        assert len(TipoDado) == 3
        assert {t.value for t in TipoDado} == {"comum", "sensivel", "crianca"}


class TestDireitosTitular:
    def test_has_ten_direitos(self) -> None:
        # Art. 18 incisos I a IX + paragrafo 2 (oposicao) = 10
        assert len(DIREITOS_TITULAR) == 10

    def test_all_direitos_are_frozen_dataclass(self) -> None:
        for d in DIREITOS_TITULAR:
            assert isinstance(d, DireitoTitular)

    def test_default_prazo_is_15_days(self) -> None:
        d = DireitoTitular(codigo="x", artigo="Art. 18 X", descricao="...")
        assert d.prazo_resposta_dias == 15

    def test_codigos_are_unique(self) -> None:
        codigos = [d.codigo for d in DIREITOS_TITULAR]
        assert len(codigos) == len(set(codigos))

    def test_contains_required_codigos(self) -> None:
        codigos = {d.codigo for d in DIREITOS_TITULAR}
        required = {
            "confirmacao",
            "acesso",
            "correcao",
            "anonimizacao",
            "portabilidade",
            "eliminacao",
            "informacao_compartilhamento",
            "informacao_consequencias",
            "revogacao_consentimento",
            "oposicao",
        }
        assert required <= codigos


class TestValidarOperacao:
    def test_sensivel_com_consentimento_valido(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="leitura_prontuario",
            tipos_dados=[TipoDado.SENSIVEL],
            base_legal=BaseLegal.CONSENTIMENTO,
            finalidade="atendimento medico",
        )
        valido, avisos = validar_operacao(op)
        assert valido is True
        assert avisos == []

    def test_sensivel_com_tutela_saude_valido(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="diagnostico",
            tipos_dados=[TipoDado.SENSIVEL],
            base_legal=BaseLegal.TUTELA_SAUDE,
            finalidade="tutela da saude do paciente",
        )
        valido, _ = validar_operacao(op)
        assert valido is True

    def test_sensivel_com_legitimo_interesse_invalido(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="profiling",
            tipos_dados=[TipoDado.SENSIVEL],
            base_legal=BaseLegal.LEGITIMO_INTERESSE,
            finalidade="marketing direcionado",
        )
        valido, avisos = validar_operacao(op)
        assert valido is False
        assert any("Art. 11" in a for a in avisos)

    def test_sensivel_com_execucao_contrato_invalido(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="x",
            tipos_dados=[TipoDado.SENSIVEL],
            base_legal=BaseLegal.EXECUCAO_CONTRATO,
            finalidade="execucao contratual",
        )
        valido, avisos = validar_operacao(op)
        assert valido is False
        assert any("Art. 11" in a for a in avisos)

    def test_finalidade_vazia_invalido(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="leitura",
            tipos_dados=[TipoDado.COMUM],
            base_legal=BaseLegal.EXECUCAO_CONTRATO,
            finalidade="",
        )
        valido, avisos = validar_operacao(op)
        assert valido is False
        assert any("Art. 6 I" in a for a in avisos)

    def test_finalidade_whitespace_invalido(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="leitura",
            tipos_dados=[TipoDado.COMUM],
            base_legal=BaseLegal.EXECUCAO_CONTRATO,
            finalidade="   ",
        )
        valido, avisos = validar_operacao(op)
        assert valido is False
        assert any("Art. 6 I" in a for a in avisos)

    def test_crianca_warn_consentimento_parental(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="cadastro",
            tipos_dados=[TipoDado.CRIANCA],
            base_legal=BaseLegal.CONSENTIMENTO,
            finalidade="cadastro escolar",
        )
        valido, avisos = validar_operacao(op)
        # warn nao invalida automaticamente - apenas alerta
        assert valido is True
        assert any("Art. 14" in a for a in avisos)
        assert any("consentimento" in a.lower() for a in avisos)

    def test_necessario_false_warn_minimizacao(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="coleta_extra",
            tipos_dados=[TipoDado.COMUM],
            base_legal=BaseLegal.EXECUCAO_CONTRATO,
            finalidade="execucao",
            necessario=False,
        )
        valido, avisos = validar_operacao(op)
        assert valido is True
        assert any("Art. 6 III" in a for a in avisos)

    def test_operacao_comum_valida_sem_avisos(self) -> None:
        op = OperacaoTratamento(
            tipo_operacao="calc_prazo",
            tipos_dados=[TipoDado.COMUM],
            base_legal=BaseLegal.EXECUCAO_CONTRATO,
            finalidade="calculo de prazo processual",
            necessario=True,
        )
        valido, avisos = validar_operacao(op)
        assert valido is True
        assert avisos == []


class TestConstantes:
    def test_prazo_resposta_titular(self) -> None:
        assert PRAZO_RESPOSTA_TITULAR_DIAS == 15

    def test_prazo_incidente_anpd(self) -> None:
        assert PRAZO_INCIDENTE_ANPD_DIAS == 2
