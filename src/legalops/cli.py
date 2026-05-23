"""CLI do LegalOps BR.

Uso:
    uv run python -m legalops.cli redact --input email.txt
    uv run python -m legalops.cli parse --input email.txt
    uv run python -m legalops.cli pipeline --input email.txt --audit-db audit.db
    uv run python -m legalops.cli audit verify --db audit.db
    uv run python -m legalops.cli audit list --db audit.db
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path

from legalops.eml_reader import read_eml_dir
from legalops.oab_sigilo import AuditLog
from legalops.orchestrator import process_email, urgentes
from legalops.pii_redactor import PIIRedactor
from legalops.tjpr_parser import parse_email
from legalops.whatsapp_notifier import WhatsAppNotifier, WhatsAppNotifierError


def _read_input(arg_input: str | None) -> str:
    if arg_input:
        return Path(arg_input).read_text(encoding="utf-8")
    return sys.stdin.read()


def _json_default(obj: object) -> object:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, tuple):
        return list(obj)
    return str(obj)


def _dump(obj: object) -> str:
    return json.dumps(obj, default=_json_default, ensure_ascii=False, indent=2)


def cmd_redact(args: argparse.Namespace) -> int:
    text = _read_input(args.input)
    result = PIIRedactor().redact(text)
    if args.json:
        print(
            _dump(
                {
                    "redacted_text": result.redacted_text,
                    "matches": len(result.matches),
                    "types": sorted({m.pii_type for m in result.matches}),
                }
            )
        )
    else:
        print(result.redacted_text)
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    text = _read_input(args.input)
    result = parse_email(text)
    print(
        _dump(
            {
                "total": result.total,
                "erros": result.erros,
                "intimacoes": [
                    {
                        "numero_processo": i.numero_processo,
                        "vara": i.vara,
                        "comarca": i.comarca,
                        "tipo_ato": i.tipo_ato,
                        "data_publicacao": i.data_publicacao.isoformat()
                        if i.data_publicacao
                        else None,
                        "prazo_textual": i.prazo_textual,
                        "prazo_dias": i.prazo_dias,
                    }
                    for i in result.intimacoes
                ],
            }
        )
    )
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    text = _read_input(args.input)
    hoje = date.fromisoformat(args.hoje) if args.hoje else None
    audit_log = AuditLog(Path(args.audit_db)) if args.audit_db else None

    results = process_email(
        text,
        parte=args.parte,
        via_dje=args.via_dje,
        hoje=hoje,
        audit_log=audit_log,
    )

    out = [
        {
            "numero_processo": r.numero_processo,
            "pii_matches": r.pii_matches,
            "tipo_ato": r.parsed.tipo_ato,
            "data_publicacao": r.parsed.data_publicacao.isoformat()
            if r.parsed.data_publicacao
            else None,
            "prazo_dias": r.parsed.prazo_dias,
            "calc": {
                "dies_a_quo": r.prazo.dies_a_quo.isoformat() if r.prazo else None,
                "dies_ad_quem": r.prazo.dies_ad_quem.isoformat() if r.prazo else None,
                "dias_uteis_restantes": r.prazo.dias_uteis_restantes_hoje
                if r.prazo
                else None,
                "alerta": r.prazo.alerta if r.prazo else None,
                "prazo_efetivo_dias": r.prazo.prazo_efetivo_dias if r.prazo else None,
                "fundamentos": list(r.prazo.fundamentos_aplicados) if r.prazo else [],
            },
            "audit_seq": r.audit_entry_seq,
            "erros": r.erros,
        }
        for r in results
    ]
    print(_dump({"count": len(out), "results": out}))
    return 0 if results else 1


def cmd_batch(args: argparse.Namespace) -> int:
    """Processa diretorio de .eml files via pipeline completo."""
    directory = Path(args.dir)
    hoje = date.fromisoformat(args.hoje) if args.hoje else None
    audit_log = AuditLog(Path(args.audit_db)) if args.audit_db else None

    emails = read_eml_dir(directory)
    results_out: list[dict[str, object]] = []
    n_intimacoes = 0

    for eml in emails:
        # Inject header Date no body se nao tiver data inline (tjpr_parser precisa)
        body = eml.body_text
        if eml.date is not None:
            body = f"Data: {eml.date.date().isoformat()}\n{body}"

        processed = process_email(
            body,
            parte=args.parte,
            via_dje=args.via_dje,
            hoje=hoje,
            audit_log=audit_log,
        )
        n_intimacoes += len(processed)

        results_out.append(
            {
                "eml_path": eml.source_path,
                "subject": eml.subject,
                "sender": eml.sender,
                "date": eml.date.isoformat() if eml.date else None,
                "n_attachments": eml.attachments_count,
                "processed": [
                    {
                        "numero_processo": r.numero_processo,
                        "pii_matches": r.pii_matches,
                        "tipo_ato": r.parsed.tipo_ato,
                        "prazo_dias": r.parsed.prazo_dias,
                        "calc": {
                            "dies_a_quo": r.prazo.dies_a_quo.isoformat()
                            if r.prazo
                            else None,
                            "dies_ad_quem": r.prazo.dies_ad_quem.isoformat()
                            if r.prazo
                            else None,
                            "alerta": r.prazo.alerta if r.prazo else None,
                        },
                        "audit_seq": r.audit_entry_seq,
                        "erros": r.erros,
                    }
                    for r in processed
                ],
            }
        )

    print(
        _dump(
            {
                "batch_dir": str(directory),
                "n_emails": len(emails),
                "n_intimacoes": n_intimacoes,
                "results": results_out,
            }
        )
    )
    return 0 if emails else 1


def cmd_notify(args: argparse.Namespace) -> int:
    """Roda pipeline em email e envia lembrete WhatsApp se houver urgentes."""
    text = _read_input(args.input)
    hoje = date.fromisoformat(args.hoje) if args.hoje else None
    audit_log = AuditLog(Path(args.audit_db)) if args.audit_db else None

    results = process_email(
        text,
        parte=args.parte,
        via_dje=args.via_dje,
        hoje=hoje,
        audit_log=audit_log,
    )

    u = urgentes(results)
    if not u:
        print(_dump({"sent": False, "reason": "no_urgentes", "checked": len(results)}))
        return 0

    notifier = WhatsAppNotifier(
        chat_id=args.chat_id,
        base_url=args.bridge_url,
        timeout=args.timeout,
    )

    if args.dry_run:
        msg = notifier.format_urgentes_message(u, hoje=hoje)
        print(_dump({"sent": False, "dry_run": True, "message": msg, "urgent_count": len(u)}))
        return 0

    try:
        sent_msg = notifier.notify_urgentes(u, hoje=hoje)
    except WhatsAppNotifierError as e:
        print(_dump({"sent": False, "error": str(e), "urgent_count": len(u)}))
        return 2

    # u nao-vazio garante msg nao-None
    assert sent_msg is not None
    print(_dump({"sent": True, "urgent_count": len(u), "message": sent_msg}))
    return 0


def cmd_audit_verify(args: argparse.Namespace) -> int:
    log = AuditLog(Path(args.db))
    valid = log.verify_chain()
    total = len(log.all())
    print(_dump({"valid": valid, "entries": total}))
    return 0 if valid else 1


def cmd_audit_list(args: argparse.Namespace) -> int:
    log = AuditLog(Path(args.db))
    entries = log.all()
    print(
        _dump(
            [
                {
                    "seq": e.seq,
                    "timestamp": e.timestamp.isoformat(),
                    "actor": e.actor,
                    "action": e.action,
                    "resource": e.resource,
                    "metadata": e.metadata,
                    "entry_hash": e.entry_hash[:12] + "...",
                }
                for e in entries
            ]
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="legalops",
        description="LegalOps BR CLI — redact + parse + calc prazos + audit",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_redact = sub.add_parser("redact", help="Redact PII de um texto")
    p_redact.add_argument("--input", "-i", help="Arquivo (default: stdin)")
    p_redact.add_argument("--json", action="store_true", help="Output JSON com stats")
    p_redact.set_defaults(func=cmd_redact)

    p_parse = sub.add_parser("parse", help="Parse intimacoes TJPR de um email")
    p_parse.add_argument("--input", "-i")
    p_parse.set_defaults(func=cmd_parse)

    p_pipe = sub.add_parser(
        "pipeline", help="Pipeline completo: redact + parse + calc + audit"
    )
    p_pipe.add_argument("--input", "-i")
    p_pipe.add_argument(
        "--parte",
        choices=["particular", "fazenda", "mp", "defensoria"],
        default="particular",
    )
    p_pipe.add_argument("--via-dje", action="store_true", help="Intimacao via DJE")
    p_pipe.add_argument("--hoje", help="Data atual ISO (default hoje)")
    p_pipe.add_argument("--audit-db", help="Caminho SQLite audit log")
    p_pipe.set_defaults(func=cmd_pipeline)

    p_batch = sub.add_parser(
        "batch", help="Processa diretorio de .eml files via pipeline"
    )
    p_batch.add_argument("--dir", required=True, help="Diretorio com arquivos .eml")
    p_batch.add_argument(
        "--parte",
        choices=["particular", "fazenda", "mp", "defensoria"],
        default="particular",
    )
    p_batch.add_argument("--via-dje", action="store_true")
    p_batch.add_argument("--hoje", help="Data atual ISO")
    p_batch.add_argument("--audit-db", help="Caminho SQLite audit log")
    p_batch.set_defaults(func=cmd_batch)

    p_notify = sub.add_parser(
        "notify", help="Pipeline + envia urgentes via WhatsApp bridge :3000"
    )
    p_notify.add_argument("--input", "-i", help="Email file (default stdin)")
    p_notify.add_argument(
        "--chat-id",
        required=True,
        help="WhatsApp chatId (ex: 5541999999999@s.whatsapp.net)",
    )
    p_notify.add_argument(
        "--bridge-url",
        default="http://localhost:3000",
        help="URL bridge.js (default: http://localhost:3000)",
    )
    p_notify.add_argument("--timeout", type=float, default=10.0)
    p_notify.add_argument("--dry-run", action="store_true", help="Nao envia, so formata")
    p_notify.add_argument(
        "--parte",
        choices=["particular", "fazenda", "mp", "defensoria"],
        default="particular",
    )
    p_notify.add_argument("--via-dje", action="store_true")
    p_notify.add_argument("--hoje", help="Data atual ISO")
    p_notify.add_argument("--audit-db", help="SQLite audit log")
    p_notify.set_defaults(func=cmd_notify)

    p_audit = sub.add_parser("audit", help="Operacoes sobre audit log")
    audit_sub = p_audit.add_subparsers(dest="audit_cmd", required=True)

    p_av = audit_sub.add_parser("verify", help="Verifica integridade SHA-256 chain")
    p_av.add_argument("--db", required=True)
    p_av.set_defaults(func=cmd_audit_verify)

    p_al = audit_sub.add_parser("list", help="Lista entries do audit log")
    p_al.add_argument("--db", required=True)
    p_al.set_defaults(func=cmd_audit_list)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
