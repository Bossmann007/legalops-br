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
from datetime import date, datetime, time
from pathlib import Path

from legalops.config import LegalOpsConfig, load_config
from legalops.contract_analyzer import analisar_contrato
from legalops.cpc_prazos import calcular_prazo
from legalops.email_notifier import EmailNotifier
from legalops.eml_reader import read_eml_dir
from legalops.metrics import MetricsRegistry
from legalops.notification_multiplex import NotificationMultiplex
from legalops.oab_sigilo import AuditLog
from legalops.orchestrator import ProcessedIntimacao, process_email, urgentes
from legalops.pii_redactor import PIIRedactor
from legalops.slack_notifier import SlackNotifier
from legalops.tjpr_parser import parse_email
from legalops.tribunal_detector import detect_tribunal
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
        sender=getattr(args, "sender", "") or "",
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
                "dias_uteis_restantes": r.prazo.dias_uteis_restantes_hoje if r.prazo else None,
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
                            "dies_a_quo": r.prazo.dies_a_quo.isoformat() if r.prazo else None,
                            "dies_ad_quem": r.prazo.dies_ad_quem.isoformat() if r.prazo else None,
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


def _parse_channels_arg(raw: str | None) -> list[str]:
    if not raw:
        return []
    out: list[str] = []
    for part in raw.split(","):
        p = part.strip().lower()
        if not p:
            continue
        if p not in ("whatsapp", "email", "slack"):
            raise ValueError(f"canal invalido: {p!r} (use whatsapp|email|slack)")
        out.append(p)
    return out


def _parse_hhmm_arg(raw: str | None) -> time | None:
    if not raw:
        return None
    try:
        hh, mm = raw.split(":")
        return time(int(hh), int(mm))
    except (ValueError, IndexError) as e:
        raise ValueError(f"formato HH:MM invalido: {raw!r}") from e


def _build_multiplex_from_args(
    args: argparse.Namespace,
    cfg: LegalOpsConfig,
    channels: list[str],
) -> NotificationMultiplex:
    quiet_start: time | None = (
        _parse_hhmm_arg(getattr(args, "quiet_start", None)) or cfg.notification_quiet_start
    )
    quiet_end: time | None = (
        _parse_hhmm_arg(getattr(args, "quiet_end", None)) or cfg.notification_quiet_end
    )
    min_prazo = getattr(args, "min_prazo_days", None)
    if min_prazo is None:
        min_prazo = cfg.notification_min_prazo_days

    mux = NotificationMultiplex(
        min_prazo_dias=int(min_prazo),
        quiet_hours_start=quiet_start,
        quiet_hours_end=quiet_end,
    )

    for ch in channels:
        if ch == "whatsapp":
            chat_id = getattr(args, "chat_id", None) or cfg.whatsapp_chat_id
            if not chat_id:
                raise ValueError("whatsapp: chat_id ausente (CLI/config)")
            wa = WhatsAppNotifier(
                chat_id=chat_id,
                base_url=getattr(args, "bridge_url", None) or cfg.whatsapp_bridge_url,
                timeout=float(getattr(args, "timeout", None) or cfg.whatsapp_timeout),
            )

            def _wa_call(
                u: list[ProcessedIntimacao],
                h: date | None,
                _n: WhatsAppNotifier = wa,
            ) -> int:
                if not u:
                    return 0
                _n.notify_urgentes(u, hoje=h)
                return len(u)

            mux.add_channel("whatsapp", _wa_call)

        elif ch == "email":
            if not (cfg.email_smtp_host and cfg.email_from_addr and cfg.email_to_addr):
                raise ValueError("email: smtp_host/from_addr/to_addr ausentes no config")
            em = EmailNotifier(
                smtp_host=cfg.email_smtp_host,
                smtp_port=cfg.email_smtp_port,
                username=cfg.email_username or "",
                password=cfg.email_password or "",
                from_addr=cfg.email_from_addr,
                use_tls=cfg.email_use_tls,
            )
            to_addr = cfg.email_to_addr

            def _em_call(
                u: list[ProcessedIntimacao],
                h: date | None,
                _n: EmailNotifier = em,
                _to: str = to_addr,
            ) -> int:
                return _n.notify_urgentes(u, to=_to, hoje=h)

            mux.add_channel("email", _em_call)

        elif ch == "slack":
            if not cfg.slack_webhook_url:
                raise ValueError("slack: webhook_url ausente no config")
            sl = SlackNotifier(
                webhook_url=cfg.slack_webhook_url,
                channel=cfg.slack_channel,
            )

            def _sl_call(
                u: list[ProcessedIntimacao],
                h: date | None,
                _n: SlackNotifier = sl,
            ) -> int:
                return _n.notify_urgentes(u, hoje=h)

            mux.add_channel("slack", _sl_call)

    return mux


def cmd_notify(args: argparse.Namespace) -> int:
    """Pipeline + envia urgentes (multi-channel se --channels passado)."""
    text = _read_input(args.input)
    hoje = date.fromisoformat(args.hoje) if args.hoje else None
    audit_log = AuditLog(Path(args.audit_db)) if args.audit_db else None

    results = process_email(
        text,
        parte=args.parte,
        via_dje=args.via_dje,
        hoje=hoje,
        audit_log=audit_log,
        sender=getattr(args, "sender", "") or "",
    )

    u = urgentes(results)
    if not u:
        print(_dump({"sent": False, "reason": "no_urgentes", "checked": len(results)}))
        return 0

    channels = _parse_channels_arg(getattr(args, "channels", None))

    if channels:
        cfg_path = Path(args.config) if getattr(args, "config", None) else None
        cfg = load_config(cfg_path)
        try:
            mux = _build_multiplex_from_args(args, cfg, channels)
        except ValueError as e:
            print(_dump({"sent": False, "error": str(e), "urgent_count": len(u)}))
            return 2

        if args.dry_run:
            print(
                _dump(
                    {
                        "sent": False,
                        "dry_run": True,
                        "channels": channels,
                        "urgent_count": len(u),
                    }
                )
            )
            return 0

        counts = mux.notify_all(u, hoje=hoje)
        print(
            _dump(
                {
                    "sent": True,
                    "urgent_count": len(u),
                    "channels": counts,
                }
            )
        )
        return 0

    # Backwards-compat: single WhatsApp channel.
    if not args.chat_id:
        print(
            _dump(
                {
                    "sent": False,
                    "error": "chat_id ausente (passe --chat-id ou configure [whatsapp])",
                }
            )
        )
        return 2
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


def _run_health_checks(audit_db: str | None) -> tuple[list[dict[str, object]], MetricsRegistry]:
    import time

    from legalops.cpc_prazos import PrazoInput

    registry = MetricsRegistry()
    checks: list[dict[str, object]] = []

    from collections.abc import Callable as _Callable

    def _run(name: str, fn: _Callable[[], None]) -> None:
        t0 = time.perf_counter()
        ok = False
        err: str | None = None
        try:
            fn()
            ok = True
        except Exception as e:  # noqa: BLE001 - health check converts all to status
            err = f"{type(e).__name__}: {e}"
        ms = round((time.perf_counter() - t0) * 1000.0, 3)
        entry: dict[str, object] = {"name": name, "ok": ok, "ms": ms}
        if err is not None:
            entry["error"] = err
        registry.counter(
            "legalops_healthcheck_total",
            1,
            labels={"check": name, "ok": "true" if ok else "false"},
        )
        registry.histogram(
            "legalops_healthcheck_seconds",
            ms / 1000.0,
            labels={"check": name},
        )
        checks.append(entry)

    def _pii_check() -> None:
        r = PIIRedactor().redact("CPF 123.456.789-09 contato test@example.com")
        if not r.has_pii:
            raise RuntimeError("PIIRedactor.has_pii=False on synthetic input")

    def _prazo_check() -> None:
        from datetime import date as _date

        calcular_prazo(
            PrazoInput(
                data_publicacao=_date(2025, 5, 5),
                prazo_dias=15,
                parte="particular",
            ),
            hoje=_date(2025, 5, 20),
        )

    def _tribunal_check() -> None:
        sample = "Tribunal de Justica do Parana — Projudi notificacao processo"
        t = detect_tribunal(sample, sender="x@tjpr.jus.br")
        if t != "tjpr":
            raise RuntimeError(f"tribunal_detector returned {t!r}, expected 'tjpr'")

    _run("pii_redactor", _pii_check)
    _run("cpc_prazos", _prazo_check)
    _run("tribunal_detector", _tribunal_check)

    if audit_db:

        def _audit_check() -> None:
            log = AuditLog(Path(audit_db))
            if not log.verify_chain():
                raise RuntimeError("audit chain verify failed")

        _run("audit_chain", _audit_check)

    return checks, registry


def cmd_health(args: argparse.Namespace) -> int:
    checks, registry = _run_health_checks(getattr(args, "audit_db", None))
    healthy = all(bool(c["ok"]) for c in checks)
    status = "healthy" if healthy else "unhealthy"
    payload = {"status": status, "checks": checks}

    if args.format == "json":
        print(_dump(payload))
    else:
        print(f"status: {status}")
        for c in checks:
            mark = "OK" if c["ok"] else "FAIL"
            line = f"  [{mark}] {c['name']} ({c['ms']} ms)"
            if not c["ok"]:
                line += f" — {c.get('error', '')}"
            print(line)

    if getattr(args, "metrics", False):
        print("\n--- metrics ---")
        print(registry.render(), end="")

    return 0 if healthy else 1


def cmd_metrics(args: argparse.Namespace) -> int:
    """Run synthetic pipeline + render Prometheus exposition."""
    import time
    from datetime import date as _date

    registry = MetricsRegistry()

    sample = (
        "Tribunal de Justica do Parana - Projudi\n"
        "Data: 2025-05-05\n"
        "Processo 0001234-56.2024.8.16.0001 - Vara Civel de Curitiba\n"
        "Intimacao para contestar no prazo de 15 dias.\n"
    )

    t0 = time.perf_counter()
    results = process_email(
        sample,
        parte="particular",
        via_dje=False,
        hoje=_date(2025, 5, 20),
        sender="dje@tjpr.jus.br",
    )
    elapsed = time.perf_counter() - t0

    registry.counter("legalops_pipeline_runs_total", 1, labels={"status": "ok"})
    registry.counter(
        "legalops_intimacoes_processed_total",
        float(len(results)),
        labels={"tribunal": "tjpr"},
    )
    registry.gauge("legalops_last_run_results", float(len(results)))
    registry.histogram("legalops_pipeline_duration_seconds", elapsed)

    print(registry.render(), end="")
    return 0


def cmd_contract(args: argparse.Namespace) -> int:
    """Analisa risco de um contrato (Contract AI — fase v1.2).

    LGPD: por padrao redige PII antes da analise. ``--skip-redact`` so deve ser
    usado quando o texto ja passou pelo redactor.
    """
    text = _read_input(args.input)
    if not args.skip_redact:
        text = PIIRedactor().redact(text).redacted_text
    rel = analisar_contrato(text)
    print(
        _dump(
            {
                "score": rel.score,
                "nivel": rel.nivel,
                "clausulas": rel.clausulas,
                "financiamento": rel.financiamento,
                "recomendacoes": rel.recomendacoes,
            }
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    from legalops import __version__

    p = argparse.ArgumentParser(
        prog="legalops",
        description="LegalOps BR CLI — redact + parse + calc prazos + audit",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"legalops {__version__}",
    )
    p.add_argument(
        "--config",
        help="Path TOML config (default ~/.config/legalops/config.toml se existir)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_redact = sub.add_parser("redact", help="Redact PII de um texto")
    p_redact.add_argument("--input", "-i", help="Arquivo (default: stdin)")
    p_redact.add_argument("--json", action="store_true", help="Output JSON com stats")
    p_redact.set_defaults(func=cmd_redact)

    p_parse = sub.add_parser("parse", help="Parse intimacoes TJPR de um email")
    p_parse.add_argument("--input", "-i")
    p_parse.set_defaults(func=cmd_parse)

    p_pipe = sub.add_parser("pipeline", help="Pipeline completo: redact + parse + calc + audit")
    p_pipe.add_argument("--input", "-i")
    p_pipe.add_argument(
        "--parte",
        choices=["particular", "fazenda", "mp", "defensoria"],
        default="particular",
    )
    p_pipe.add_argument("--via-dje", action="store_true", help="Intimacao via DJE")
    p_pipe.add_argument("--hoje", help="Data atual ISO (default hoje)")
    p_pipe.add_argument("--audit-db", help="Caminho SQLite audit log")
    p_pipe.add_argument(
        "--sender",
        default="",
        help="Email From: header (forca deteccao tribunal por domain, ex: x@tjsp.jus.br)",
    )
    p_pipe.set_defaults(func=cmd_pipeline)

    p_batch = sub.add_parser("batch", help="Processa diretorio de .eml files via pipeline")
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

    p_notify = sub.add_parser("notify", help="Pipeline + envia urgentes via WhatsApp bridge :3000")
    p_notify.add_argument("--input", "-i", help="Email file (default stdin)")
    p_notify.add_argument(
        "--chat-id",
        default=None,
        help="WhatsApp chatId (obrigatorio se canal whatsapp e sem config)",
    )
    p_notify.add_argument(
        "--channels",
        default=None,
        help="Lista canais separados por virgula: whatsapp,email,slack",
    )
    p_notify.add_argument(
        "--min-prazo-days",
        type=int,
        default=None,
        help="Threshold: so notifica prazos <= N dias uteis (default 3)",
    )
    p_notify.add_argument(
        "--quiet-start",
        default=None,
        help="Inicio quiet hours HH:MM (sem notificacoes na janela)",
    )
    p_notify.add_argument(
        "--quiet-end",
        default=None,
        help="Fim quiet hours HH:MM",
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
    p_notify.add_argument(
        "--sender",
        default="",
        help="Email From: header (forca deteccao tribunal)",
    )
    p_notify.set_defaults(func=cmd_notify)

    p_audit = sub.add_parser("audit", help="Operacoes sobre audit log")
    audit_sub = p_audit.add_subparsers(dest="audit_cmd", required=True)

    p_av = audit_sub.add_parser("verify", help="Verifica integridade SHA-256 chain")
    p_av.add_argument("--db", required=True)
    p_av.set_defaults(func=cmd_audit_verify)

    p_al = audit_sub.add_parser("list", help="Lista entries do audit log")
    p_al.add_argument("--db", required=True)
    p_al.set_defaults(func=cmd_audit_list)

    p_contract = sub.add_parser(
        "contract", help="Analisa risco de contrato (clausulas abusivas CDC + financiamento)"
    )
    p_contract.add_argument("--input", "-i", help="Arquivo (default: stdin)")
    p_contract.add_argument(
        "--skip-redact",
        action="store_true",
        help="Pula redacao de PII (use so se texto ja redigido)",
    )
    p_contract.set_defaults(func=cmd_contract)

    p_health = sub.add_parser("health", help="Health checks dos componentes core")
    p_health.add_argument("--format", choices=["json", "text"], default="text")
    p_health.add_argument("--audit-db", help="Se dado, valida AuditLog.verify_chain()")
    p_health.add_argument("--metrics", action="store_true", help="Render metrics apos checks")
    p_health.set_defaults(func=cmd_health)

    p_metrics = sub.add_parser(
        "metrics",
        help="Renderiza Prometheus exposition de um pipeline sintetico",
    )
    p_metrics.set_defaults(func=cmd_metrics)

    return p


def _apply_config_defaults(args: argparse.Namespace) -> None:
    """Override args com valores do config TOML quando flag CLI nao explicita."""
    cfg_path = Path(args.config) if getattr(args, "config", None) else None
    cfg = load_config(cfg_path)

    if hasattr(args, "parte") and args.parte == "particular":
        args.parte = cfg.parte
    if hasattr(args, "via_dje") and not args.via_dje:
        args.via_dje = cfg.via_dje
    if hasattr(args, "audit_db") and not args.audit_db and cfg.audit_db:
        args.audit_db = cfg.audit_db
    if hasattr(args, "bridge_url") and args.bridge_url == "http://localhost:3000":
        args.bridge_url = cfg.whatsapp_bridge_url
    if hasattr(args, "chat_id") and not args.chat_id and cfg.whatsapp_chat_id:
        args.chat_id = cfg.whatsapp_chat_id


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _apply_config_defaults(args)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
