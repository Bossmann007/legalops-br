"""Tests para orchestrator — pipeline end-to-end com emails sinteticos."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from legalops.oab_sigilo import AuditLog
from legalops.orchestrator import (
    ProcessedIntimacao,
    por_alerta,
    process_email,
    urgentes,
)

EMAIL_BASICO = (
    "De: projudisistema@tjpr.jus.br\n"
    "Data: 21/05/2026\n"
    "Processo 0001234-56.2026.8.16.0001\n"
    "Despacho: Intime-se a parte re para contestar no prazo de 15 dias uteis.\n"
)

EMAIL_COM_PII = (
    "De: projudisistema@tjpr.jus.br\n"
    "Data: 21/05/2026\n"
    "Processo 0009999-11.2026.8.16.0001\n"
    "Procurador OAB/PR 12345 (CPF 123.456.789-00)\n"
    "Cliente CNPJ 12.345.678/0001-90\n"
    "Despacho: prazo de 10 dias uteis.\n"
)

EMAIL_MULTI = (
    "De: projudisistema@tjpr.jus.br\n"
    "Data: 22/05/2026\n"
    "Processo 0001111-11.2026.8.16.0001\n"
    "Despacho: prazo de 5 dias.\n"
    "===\n"
    "Processo 0002222-22.2026.8.16.0002\n"
    "Decisao: prazo de 15 dias.\n"
)

EMAIL_SEM_PROCESSO = "Email comum sem numero de processo."


class TestProcessEmailBasico:
    def test_retorna_uma_intimacao(self) -> None:
        results = process_email(EMAIL_BASICO, hoje=date(2026, 5, 22))
        assert len(results) == 1
        assert isinstance(results[0], ProcessedIntimacao)

    def test_numero_processo_correto(self) -> None:
        results = process_email(EMAIL_BASICO, hoje=date(2026, 5, 22))
        assert results[0].numero_processo == "0001234-56.2026.8.16.0001"

    def test_calcula_prazo(self) -> None:
        results = process_email(EMAIL_BASICO, hoje=date(2026, 5, 22))
        assert results[0].prazo is not None
        assert results[0].prazo.prazo_efetivo_dias == 15

    def test_dies_a_quo_correto(self) -> None:
        results = process_email(EMAIL_BASICO, hoje=date(2026, 5, 22))
        assert results[0].prazo is not None
        assert results[0].prazo.dies_a_quo == date(2026, 5, 22)


class TestProcessEmailRedaction:
    def test_pii_redacted(self) -> None:
        results = process_email(EMAIL_COM_PII, hoje=date(2026, 5, 22))
        assert results[0].pii_matches >= 3

    def test_redacted_text_sem_cpf_bruto(self) -> None:
        results = process_email(EMAIL_COM_PII, hoje=date(2026, 5, 22))
        assert "123.456.789-00" not in results[0].redacted_text

    def test_redacted_text_sem_cnpj_bruto(self) -> None:
        results = process_email(EMAIL_COM_PII, hoje=date(2026, 5, 22))
        assert "12.345.678/0001-90" not in results[0].redacted_text


class TestProcessEmailMulti:
    def test_dois_processos(self) -> None:
        results = process_email(EMAIL_MULTI, hoje=date(2026, 5, 23))
        assert len(results) == 2

    def test_processos_diferentes(self) -> None:
        results = process_email(EMAIL_MULTI, hoje=date(2026, 5, 23))
        numeros = {r.numero_processo for r in results}
        assert "0001111-11.2026.8.16.0001" in numeros
        assert "0002222-22.2026.8.16.0002" in numeros


class TestProcessEmailVazio:
    def test_sem_processo_retorna_vazio(self) -> None:
        results = process_email(EMAIL_SEM_PROCESSO)
        assert results == []

    def test_texto_vazio_retorna_vazio(self) -> None:
        results = process_email("")
        assert results == []


class TestDobroFazenda:
    def test_fazenda_aplica_dobro(self) -> None:
        results = process_email(
            EMAIL_BASICO, parte="fazenda", hoje=date(2026, 5, 22)
        )
        assert results[0].prazo is not None
        assert results[0].prazo.prazo_efetivo_dias == 30

    def test_mp_aplica_dobro(self) -> None:
        results = process_email(EMAIL_BASICO, parte="mp", hoje=date(2026, 5, 22))
        assert results[0].prazo is not None
        assert results[0].prazo.prazo_efetivo_dias == 30


class TestDJE:
    def test_via_dje_pula_dia(self) -> None:
        results = process_email(
            EMAIL_BASICO, via_dje=True, hoje=date(2026, 5, 22)
        )
        assert results[0].prazo is not None
        assert results[0].prazo.data_intimacao_considerada == date(2026, 5, 22)
        assert results[0].prazo.dies_a_quo == date(2026, 5, 25)


class TestAuditLogIntegration:
    def test_audit_recebe_entries(self, tmp_path: Path) -> None:
        db = tmp_path / "audit.db"
        log = AuditLog(db)
        process_email(EMAIL_BASICO, hoje=date(2026, 5, 22), audit_log=log)
        entries = log.all()
        assert len(entries) >= 3
        actions = {e.action for e in entries}
        assert "redact" in actions
        assert "parse" in actions
        assert "calc_prazo" in actions

    def test_audit_seq_no_resultado(self, tmp_path: Path) -> None:
        db = tmp_path / "audit.db"
        log = AuditLog(db)
        results = process_email(
            EMAIL_BASICO, hoje=date(2026, 5, 22), audit_log=log
        )
        assert results[0].audit_entry_seq is not None
        assert results[0].audit_entry_seq > 0

    def test_audit_chain_valido(self, tmp_path: Path) -> None:
        db = tmp_path / "audit.db"
        log = AuditLog(db)
        process_email(EMAIL_BASICO, hoje=date(2026, 5, 22), audit_log=log)
        assert log.verify_chain() is True

    def test_sem_audit_log_funciona(self) -> None:
        results = process_email(EMAIL_BASICO, hoje=date(2026, 5, 22))
        assert results[0].audit_entry_seq is None


class TestFiltros:
    def test_urgentes_filtra_corretamente(self) -> None:
        results = process_email(EMAIL_BASICO, hoje=date(2026, 5, 22))
        u = urgentes(results)
        assert len(u) == 0

    def test_por_alerta_chaves(self) -> None:
        results = process_email(EMAIL_BASICO, hoje=date(2026, 5, 22))
        grupos = por_alerta(results)
        assert "URGENTE" in grupos
        assert "ATENCAO" in grupos
        assert "NORMAL" in grupos
        assert "SEM_PRAZO" in grupos

    def test_por_alerta_total_preservado(self) -> None:
        results = process_email(EMAIL_MULTI, hoje=date(2026, 5, 23))
        grupos = por_alerta(results)
        total = sum(len(v) for v in grupos.values())
        assert total == len(results)


class TestErroHandling:
    def test_email_sem_data_skip_calc_prazo(self) -> None:
        txt = "Processo 0001234-56.2026.8.16.0001\nDespacho sem data nem prazo."
        results = process_email(txt)
        assert len(results) == 1
        assert results[0].prazo is None
        assert len(results[0].erros) >= 1
