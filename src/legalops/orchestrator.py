"""Orchestrator do pipeline LegalOps BR.

Encadeia os modulos core em uma chamada unica:
    email_text -> pii_redactor -> tjpr_parser -> cpc_prazos -> oab_sigilo (audit)

Uso:
    from legalops.orchestrator import process_email
    results = process_email(email_text, parte="particular", hoje=date(2026,5,23))
    for r in results:
        print(r.numero_processo, r.prazo.dies_ad_quem if r.prazo else "(sem prazo)")
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from legalops.cpc_prazos import (
    ParteType,
    PrazoInput,
    PrazoResult,
    calcular_prazo,
)
from legalops.oab_sigilo import AuditLog
from legalops.pii_redactor import PIIRedactor
from legalops.tjpr_parser import Intimacao, ParseResult
from legalops.tjpr_parser import parse_email as parse_tjpr
from legalops.tjrj_parser import parse_email as parse_tjrj
from legalops.tjsc_parser import parse_email as parse_tjsc
from legalops.tjsp_parser import parse_email as parse_tjsp
from legalops.tribunal_detector import detect_tribunal

_PARSERS: dict[str, Callable[[str], ParseResult]] = {
    "tjsp": parse_tjsp,
    "tjsc": parse_tjsc,
    "tjrj": parse_tjrj,
    "tjpr": parse_tjpr,
}


@dataclass
class ProcessedIntimacao:
    """Resultado do pipeline aplicado a UMA intimacao."""

    numero_processo: str
    redacted_text: str
    pii_matches: int
    parsed: Intimacao
    prazo: PrazoResult | None = None
    audit_entry_seq: int | None = None
    erros: list[str] = field(default_factory=list)


def process_email(
    email_text: str,
    *,
    parte: ParteType = "particular",
    via_dje: bool = False,
    hoje: date | None = None,
    audit_log: AuditLog | None = None,
    redactor_salt: str = "legalops-br-v0.1",
    sender: str = "",
) -> list[ProcessedIntimacao]:
    """Roda pipeline completo em um email.

    Args:
        email_text: texto bruto do email TJPR/Projudi.
        parte: tipo da parte (particular/fazenda/mp/defensoria).
        via_dje: se True, aplica Art. 231 #1 (intimacao eletronica).
        hoje: data atual (default date.today()) — util pra testes deterministicos.
        audit_log: opcional AuditLog pra registrar cada operacao.
        redactor_salt: salt do PIIRedactor (override pra testes).

    Returns:
        Lista de ProcessedIntimacao, uma por processo encontrado no email.
        Lista vazia se nenhum processo CNJ identificado.
    """
    redactor = PIIRedactor(salt=redactor_salt)

    redacted = redactor.redact(email_text)
    if audit_log is not None:
        audit_log.append(
            actor="orchestrator",
            action="redact",
            resource="email:inbox",
            metadata={"pii_matches": len(redacted.matches)},
        )

    tribunal = detect_tribunal(email_text, sender=sender)
    _parse = _PARSERS.get(tribunal, parse_tjpr)
    parse_result = _parse(redacted.redacted_text)
    if audit_log is not None:
        audit_log.append(
            actor="orchestrator",
            action="parse",
            resource="email:inbox",
            metadata={"intimacoes_found": parse_result.total, "tribunal": tribunal},
        )

    results: list[ProcessedIntimacao] = []

    for intim in parse_result.intimacoes:
        item = ProcessedIntimacao(
            numero_processo=intim.numero_processo,
            redacted_text=redacted.redacted_text,
            pii_matches=len(redacted.matches),
            parsed=intim,
        )

        if intim.prazo_dias is not None and intim.data_publicacao is not None:
            try:
                prazo = calcular_prazo(
                    PrazoInput(
                        data_publicacao=intim.data_publicacao,
                        prazo_dias=intim.prazo_dias,
                        parte=parte,
                        via_dje=via_dje,
                    ),
                    hoje=hoje,
                )
                item.prazo = prazo
                if audit_log is not None:
                    entry = audit_log.append(
                        actor="orchestrator",
                        action="calc_prazo",
                        resource=f"process:{intim.numero_processo}",
                        metadata={
                            "dies_a_quo": prazo.dies_a_quo.isoformat(),
                            "dies_ad_quem": prazo.dies_ad_quem.isoformat(),
                            "alerta": prazo.alerta,
                        },
                    )
                    item.audit_entry_seq = entry.seq
            except (ValueError, KeyError) as e:
                item.erros.append(f"calc_prazo: {e}")
        else:
            item.erros.append("Sem prazo_dias ou data_publicacao — skip calc_prazo")

        results.append(item)

    return results


def urgentes(results: list[ProcessedIntimacao]) -> list[ProcessedIntimacao]:
    """Filtra apenas resultados com alerta URGENTE."""
    return [r for r in results if r.prazo is not None and r.prazo.alerta == "URGENTE"]


def por_alerta(
    results: list[ProcessedIntimacao],
) -> dict[str, list[ProcessedIntimacao]]:
    """Agrupa resultados por nivel de alerta."""
    out: dict[str, list[ProcessedIntimacao]] = {
        "URGENTE": [],
        "ATENCAO": [],
        "NORMAL": [],
        "SEM_PRAZO": [],
    }
    for r in results:
        if r.prazo is None:
            out["SEM_PRAZO"].append(r)
        else:
            out[r.prazo.alerta].append(r)
    return out
