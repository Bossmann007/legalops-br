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
import re
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path

from legalops.anpd_playbook import Incidente, gerar_plano
from legalops.config import load_config
from legalops.contract_analyzer import analisar_contrato
from legalops.cpc_prazos import (
    RECESSO_POR_TRIBUNAL,
    PrazoInput,
    PrazoResult,
    calcular_prazo,
    is_recesso_forense,
)
from legalops.disclosure import (
    DisclosureItem,
    DisclosureSchedule,
    Representacao,
    find_gaps,
    inconsistencias,
)
from legalops.doc_extractor import (
    ContratoHonorariosCampos,
    ProcuracaoCampos,
    extract_contrato_honorarios,
    extract_procuracao,
)
from legalops.doc_templates import render_contrato_honorarios, render_procuracao
from legalops.dpa_templates import DPAParams, render_dpa
from legalops.dsar import DSARError, DSARRequest, classify_request, processar_dsar
from legalops.due_diligence import checklist_padrao
from legalops.eml_reader import read_eml_dir
from legalops.lgpd_specifics import (
    DIREITOS_TITULAR,
    BaseLegal,
    OperacaoTratamento,
    TipoDado,
)
from legalops.metrics import MetricsRegistry
from legalops.oab_sigilo import AuditLog
from legalops.orchestrator import process_email
from legalops.pia import avaliar_ripd
from legalops.pii_redactor import MissingSaltError, PIIRedactor
from legalops.red_flags import scan_acquisition_contract
from legalops.renewal_watcher import Contrato, RenewalWatcher
from legalops.societario import (
    EstruturaSocietaria,
    Socio,
    validar_participacoes,
)
from legalops.tjpr_parser import parse_email
from legalops.tribunal_detector import detect_tribunal
from legalops.vendor_ai_review import checklist_vendor_padrao


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


_STRICT_RESIDUAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("CNPJ", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
    ("CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("OAB", re.compile(r"\bOAB[/-]?[A-Z]{2}\s?\d{1,6}\b")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("PHONE_BR", re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}-\d{4}\b")),
    ("CNPJ_NUMERIC", re.compile(r"\b\d{14}\b")),
    ("CPF_NUMERIC", re.compile(r"\b\d{11}\b")),
)


def _scan_residual_pii(text: str) -> list[dict[str, object]]:
    residual: list[dict[str, object]] = []
    hits: list[tuple[int, int, str]] = []
    seen_spans: set[tuple[int, int]] = set()
    for pii_type, pattern in _STRICT_RESIDUAL_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if any(start < e and s < end for s, e in seen_spans):
                continue
            seen_spans.add((start, end))
            hits.append((start, end, pii_type))
    for start, end, pii_type in sorted(hits):
        residual.append({"tipo": pii_type, "span": (start, end)})
    return residual


PRAZOS_LEDGER_PATH = Path("data/prazos.json")
HONORARIOS_LEDGER_PATH = Path("data/honorarios.json")
CLIENTES_LEDGER_PATH = Path("data/clientes.json")


def _prazo_to_json(
    inp: PrazoInput,
    result: PrazoResult,
    *,
    aviso_tribunal: str | None = None,
) -> dict[str, object]:
    data = asdict(result)
    data["fundamentos_aplicados"] = list(data["fundamentos_aplicados"])
    data["tribunal"] = inp.tribunal
    data["data_final"] = data["dies_ad_quem"]
    data["dias_corridos"] = (data["dies_ad_quem"] - data["data_publicacao"]).days
    fundamentos = " ".join(data["fundamentos_aplicados"])
    data["dobro_aplicado"] = data["prazo_efetivo_dias"] != inp.prazo_dias
    cur = result.data_publicacao
    recesso_aplicado = False
    while cur <= result.dies_ad_quem:
        if is_recesso_forense(cur, inp.tribunal, strict=False):
            recesso_aplicado = True
            break
        cur = date.fromordinal(cur.toordinal() + 1)
    data["recesso_aplicado"] = recesso_aplicado
    data["flags"] = {
        "dobro_aplicado": "em dobro" in fundamentos,
        "recesso_aplicado": recesso_aplicado,
    }
    if aviso_tribunal:
        data["aviso_tribunal"] = aviso_tribunal
    return data


def _load_prazos_ledger(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    if not path.exists():
        return [], [f"{path} ausente; nenhum prazo local registrado"]
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("prazos.json deve conter uma lista")
    items: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("cada prazo deve ser um objeto JSON")
        items.append(item)
    return items, []


def _save_prazos_ledger(path: Path, items: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump(items) + "\n", encoding="utf-8")


def _append_prazo_ledger(path: Path, item: dict[str, object]) -> None:
    items, _avisos = _load_prazos_ledger(path)
    items.append(item)
    _save_prazos_ledger(path, items)


def _load_honorarios_ledger(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("honorarios.json deve conter uma lista")
    items: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("cada honorario deve ser um objeto JSON")
        items.append(item)
    return items


def _save_honorarios_ledger(path: Path, items: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump(items) + "\n", encoding="utf-8")


def _append_honorarios_ledger(path: Path, item: dict[str, object]) -> None:
    items = _load_honorarios_ledger(path)
    items.append(item)
    _save_honorarios_ledger(path, items)


def _load_clientes_ledger(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("clientes.json deve conter uma lista")
    items: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("cada cliente deve ser um objeto JSON")
        items.append(item)
    return items


def _save_clientes_ledger(path: Path, items: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump(items) + "\n", encoding="utf-8")


def _append_clientes_ledger(path: Path, item: dict[str, object]) -> None:
    items = _load_clientes_ledger(path)
    items.append(item)
    _save_clientes_ledger(path, items)


def _contrato_from_json(raw: object) -> Contrato:
    if not isinstance(raw, dict):
        raise ValueError("cada contrato deve ser um objeto JSON")
    contrato_id = raw.get("contrato_id") or raw.get("id") or raw.get("alias")
    if not isinstance(contrato_id, str) or not contrato_id:
        raise ValueError("contrato sem contrato_id/id/alias")
    alias = raw.get("alias") or contrato_id
    if not isinstance(alias, str) or not alias:
        raise ValueError(f"contrato {contrato_id} sem alias valido")
    data_inicio_raw = raw.get("data_inicio", "1970-01-01")
    data_fim_raw = raw.get("data_fim")
    if not isinstance(data_inicio_raw, str) or not isinstance(data_fim_raw, str):
        raise ValueError(f"contrato {contrato_id} exige data_inicio/data_fim ISO")
    aviso_raw = raw.get("aviso_previo_dias", 0)
    if not isinstance(aviso_raw, int):
        raise ValueError(f"contrato {contrato_id} exige aviso_previo_dias inteiro")
    auto_raw = raw.get("renovacao_automatica", False)
    if not isinstance(auto_raw, bool):
        raise ValueError(f"contrato {contrato_id} exige renovacao_automatica boolean")
    return Contrato(
        contrato_id=contrato_id,
        descricao=alias,
        data_inicio=date.fromisoformat(data_inicio_raw),
        data_fim=date.fromisoformat(data_fim_raw),
        aviso_previo_dias=aviso_raw,
        renovacao_automatica=auto_raw,
    )


def _load_contratos(path: Path) -> tuple[list[Contrato], list[str]]:
    if not path.exists():
        return [], [f"{path} ausente; nenhum contrato monitorado"]
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("contratos", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("contratos.json deve ser uma lista ou conter chave 'contratos'")
    return [_contrato_from_json(item) for item in items], []


def _make_redactor() -> PIIRedactor:
    """Cria PIIRedactor com salt secreto do ambiente.

    Sai com codigo 2 e mensagem acionavel se LEGALOPS_PII_SALT nao estiver
    definido — pseudonimizacao sem salt secreto seria reversivel.
    """
    try:
        return PIIRedactor()
    except MissingSaltError as e:
        print(f"erro: {e}", file=sys.stderr)
        raise SystemExit(2) from e


def cmd_redact(args: argparse.Namespace) -> int:
    text = _read_input(args.input)
    result = _make_redactor().redact(text)
    if args.strict:
        residual = _scan_residual_pii(result.redacted_text)
        if residual:
            print(_dump({"ok": False, "residual_pii": residual}))
            return 3
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
        r = PIIRedactor(salt="healthcheck-synthetic-salt").redact(
            "CPF 123.456.789-09 contato test@example.com"
        )
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
        text = _make_redactor().redact(text).redacted_text
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


def cmd_dsar(args: argparse.Namespace) -> int:
    """Processa requisicao de titular (DSAR — Art. 18 LGPD, fase v1.4).

    Le o texto da requisicao, redige PII por padrao, classifica o direito
    invocado e calcula prazo/SLA operacional de resposta.
    """
    text = _read_input(args.input)
    if not args.skip_redact:
        text = _make_redactor().redact(text).redacted_text

    codigo = args.direito or classify_request(text)
    if not codigo:
        print(
            _dump(
                {
                    "error": "nao foi possivel classificar o direito (use --direito)",
                    "direitos": [d.codigo for d in DIREITOS_TITULAR],
                }
            )
        )
        return 2

    recebimento = date.fromisoformat(args.recebimento) if args.recebimento else date.today()
    hoje = date.fromisoformat(args.hoje) if args.hoje else None
    req = DSARRequest(
        request_id=args.request_id,
        codigo_direito=codigo,
        data_recebimento=recebimento,
        titular_ref=args.titular_ref,
    )
    try:
        resp = processar_dsar(req, hoje=hoje)
    except DSARError as e:
        print(_dump({"error": str(e)}))
        return 2

    print(
        _dump(
            {
                "request_id": resp.request_id,
                "codigo_direito": resp.codigo_direito,
                "artigo": resp.artigo,
                "referencia_prazo": resp.referencia_prazo,
                "prazo_final": resp.prazo_final.isoformat(),
                "dias_restantes": resp.dias_restantes,
                "status": resp.status,
                "texto_resposta": resp.texto_resposta,
            }
        )
    )
    return 0


def cmd_prazo(args: argparse.Namespace) -> int:
    """Calcula prazo CPC diretamente a partir de parametros estruturados."""
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
    tribunal = args.tribunal.upper()
    aviso_tribunal = None
    strict_recesso = tribunal in RECESSO_POR_TRIBUNAL
    if not strict_recesso:
        aviso_tribunal = (
            f"Recesso/feriado forense não modelado para {tribunal}. "
            "Trate como estimativa e confira no tribunal."
        )
    inp = PrazoInput(
        data_publicacao=date.fromisoformat(args.data_publicacao),
        prazo_dias=args.prazo_dias,
        parte=args.parte,
        via_dje=args.via_dje,
        tribunal=tribunal,
    )
    result = calcular_prazo(inp, hoje=hoje, strict_recesso=strict_recesso)
    payload = _prazo_to_json(inp, result, aviso_tribunal=aviso_tribunal)
    if args.salvar:
        if not args.ref or not args.ato:
            print(_dump({"error": "--salvar exige --ref e --ato"}))
            return 2
        ledger_item: dict[str, object] = {
            "ref": args.ref,
            "ato": args.ato,
            "data_final": result.dies_ad_quem.isoformat(),
            "tribunal": tribunal,
            "criado_em": hoje.isoformat(),
            "status": "aberto",
        }
        try:
            _append_prazo_ledger(PRAZOS_LEDGER_PATH, ledger_item)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(_dump({"error": str(e), "path": str(PRAZOS_LEDGER_PATH)}))
            return 2
        payload["salvo"] = True
        payload["prazo_registrado"] = ledger_item
    print(_dump(payload))
    return 0


def cmd_validar_extracao(args: argparse.Namespace) -> int:
    """Roda o oracle sobre duas extrações e imprime o veredito JSON.

    Exit 0 = ok · Exit 3 = revisao_manual_obrigatoria · Exit 2 = erro de entrada.
    O skill ramifica pelo exit code — nunca por parse de texto.
    """
    from legalops.prazo_oracle import STATUS_OK, evaluate_extraction

    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
    try:
        a = json.loads(Path(args.file_a).read_text(encoding="utf-8"))
        b = json.loads(Path(args.file_b).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(_dump({"error": f"entrada inválida: {e}"}))
        return 2

    ledger, _avisos = _load_prazos_ledger(PRAZOS_LEDGER_PATH)
    v = evaluate_extraction(a, b, hoje=hoje, ledger=ledger)
    print(_dump({"status": v.status, "reasons": v.reasons, "campos": v.campos}))
    return 0 if v.status == STATUS_OK else 3


def cmd_calc_disponivel(args: argparse.Namespace) -> int:
    """Canário determinístico: prova que o motor de cálculo está são.

    Exit 0 + {"disponivel": true} se o cálculo-canário bate o esperado.
    Exit 1 caso contrário — o skill trata como fail-closed (RECUSA calcular).
    """
    from legalops.cpc_prazos import PrazoInput, calcular_prazo

    try:
        inp = PrazoInput(
            data_publicacao=date(2026, 3, 2),
            prazo_dias=15,
            parte="particular",
            via_dje=False,
            tribunal="TJPR",
        )
        res = calcular_prazo(inp, hoje=date(2026, 3, 2))
        esperado = date(2026, 3, 23)
        ok = res.dies_ad_quem == esperado
    except Exception as e:  # noqa: BLE001 — preflight precisa capturar qualquer falha
        print(_dump({"disponivel": False, "erro": str(e)}))
        return 1
    if not ok:
        print(
            _dump(
                {
                    "disponivel": False,
                    "erro": f"canário divergiu: obtido {res.dies_ad_quem}, esperado {esperado}",
                }
            )
        )
        return 1
    print(_dump({"disponivel": True}))
    return 0


def cmd_scan_state(args: argparse.Namespace) -> int:
    """Get: imprime o estado descrito. Set: grava o resultado da varredura."""
    from legalops.scan_state import (
        ScanState,
        describe_state,
        load_scan_state,
        save_scan_state,
    )

    if args.set:
        state = ScanState(
            ultima_varredura=args.quando,
            resultado=args.resultado,
            n_encontrados=args.n_encontrados,
            n_processados=args.n_processados,
            n_revisao=args.n_revisao,
        )
        save_scan_state(state)
        print(_dump({"salvo": True, "estado_bruto": args.resultado}))
        return 0

    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
    described = describe_state(load_scan_state(), hoje=hoje)
    print(_dump(described))
    return 0


def cmd_triagem(args: argparse.Namespace) -> int:
    """Filtra candidatos de tribunal de uma lista bruta de emails (JSON)."""
    from legalops.triagem import filtrar_candidatos

    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
    try:
        emails = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(emails, list):
            raise ValueError("input deve ser uma lista de emails")
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(_dump({"error": f"entrada inválida: {e}"}))
        return 2

    candidatos = filtrar_candidatos(emails, janela_dias=args.janela, hoje=hoje)
    print(_dump({"candidatos": candidatos, "total": len(candidatos)}))
    return 0


def cmd_prazos(args: argparse.Namespace) -> int:
    """Lista prazos locais persistidos em data/prazos.json."""
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
    try:
        items, avisos = _load_prazos_ledger(PRAZOS_LEDGER_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(_dump({"error": str(e), "path": str(PRAZOS_LEDGER_PATH)}))
        return 2

    prazos: list[dict[str, object]] = []
    for item in items:
        status = str(item.get("status", "aberto"))
        if status != "aberto" and not args.incluir_cumpridos:
            continue
        data_final_raw = item.get("data_final")
        if not isinstance(data_final_raw, str):
            continue
        data_final = date.fromisoformat(data_final_raw)
        dias_ate = (data_final - hoje).days
        if dias_ate <= args.ate:
            out = dict(item)
            out["dias_ate"] = dias_ate
            prazos.append(out)

    prazos.sort(key=lambda p: (str(p.get("data_final", "")), str(p.get("ref", ""))))
    print(_dump({"avisos": avisos, "prazos": prazos}))
    return 0


def cmd_honorarios(args: argparse.Namespace) -> int:
    """Append/list do ledger local de honorarios em data/honorarios.json."""
    try:
        if args.add:
            item: dict[str, object] = {
                "ref": args.ref,
                "descricao": args.descricao,
                "valor": float(args.valor),
                "data": date.fromisoformat(args.data).isoformat(),
                "status": args.status,
            }
            _append_honorarios_ledger(HONORARIOS_LEDGER_PATH, item)
            print(_dump(item))
            return 0

        items = _load_honorarios_ledger(HONORARIOS_LEDGER_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(_dump({"error": str(e), "path": str(HONORARIOS_LEDGER_PATH)}))
        return 2

    if args.status:
        items = [item for item in items if item.get("status") == args.status]
    total = 0.0
    for item in items:
        valor = item.get("valor", 0.0)
        if isinstance(valor, (int, float, str)):
            total += float(valor)
    print(_dump({"honorarios": items, "total": total}))
    return 0


def cmd_clientes(args: argparse.Namespace) -> int:
    """Append/list do registro alias-only em data/clientes.json."""
    try:
        if args.add:
            item: dict[str, object] = {
                "alias": args.alias,
                "area": args.area,
                "tribunal": args.tribunal,
                "obs": args.obs or "",
                "criado_em": date.today().isoformat(),
            }
            _append_clientes_ledger(CLIENTES_LEDGER_PATH, item)
            print(_dump(item))
            return 0

        items = _load_clientes_ledger(CLIENTES_LEDGER_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(_dump({"error": str(e), "path": str(CLIENTES_LEDGER_PATH)}))
        return 2

    print(_dump({"clientes": items}))
    return 0


def cmd_renovacao(args: argparse.Namespace) -> int:
    """Lista alertas de renovacao a partir de data/contratos.json."""
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
    path = Path("data/contratos.json")
    try:
        contratos, avisos = _load_contratos(path)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(_dump({"error": str(e), "path": str(path)}))
        return 2

    watcher = RenewalWatcher()
    for contrato in contratos:
        watcher.add(contrato)

    alertas = watcher.check(hoje=hoje, incluir_ok=args.incluir_ok)
    print(
        _dump(
            {
                "avisos": avisos,
                "alertas": [
                    {
                        "contrato_id": alerta.contrato_id,
                        "alias": alerta.descricao,
                        "dias_ate_evento": min(
                            d
                            for d in (
                                alerta.dias_para_vencimento,
                                alerta.dias_para_aviso,
                            )
                            if d is not None
                        ),
                        "dias_para_vencimento": alerta.dias_para_vencimento,
                        "dias_para_aviso": alerta.dias_para_aviso,
                        "urgencia": alerta.urgencia,
                        "renovacao_automatica": alerta.renovacao_automatica,
                    }
                    for alerta in alertas
                ],
            }
        )
    )
    return 0


def cmd_tribunal_detect(args: argparse.Namespace) -> int:
    """Detecta tribunal por sender + assinatura no corpo (deterministico)."""
    text = _read_input(args.input)
    # Redige PII antes de qualquer processamento de texto livre (LGPD).
    text = _make_redactor().redact(text).redacted_text
    tribunal = detect_tribunal(text, sender=getattr(args, "sender", "") or "")
    print(_dump({"tribunal": tribunal, "sender": getattr(args, "sender", "") or ""}))
    return 0


def cmd_red_flags(args: argparse.Namespace) -> int:
    """Scan de red flags em contrato de aquisicao (deterministico)."""
    text = _read_input(args.input)
    if not args.skip_redact:
        text = _make_redactor().redact(text).redacted_text
    flags = scan_acquisition_contract(text)
    print(
        _dump(
            {
                "count": len(flags),
                "flags": [
                    {
                        "tipo": f.tipo,
                        "severidade": f.severidade,
                        "trecho": f.trecho,
                        "nota": f.nota,
                    }
                    for f in flags
                ],
            }
        )
    )
    return 0


def cmd_pia(args: argparse.Namespace) -> int:
    """Avalia RIPD/PIA de uma operacao de tratamento (Art. 38 LGPD)."""
    tipos = [TipoDado(t) for t in (args.tipos_dados or [])]
    op = OperacaoTratamento(
        tipo_operacao=args.tipo_operacao,
        tipos_dados=tipos,
        base_legal=BaseLegal(args.base_legal),
        finalidade=args.finalidade,
        necessario=not args.nao_necessario,
    )
    ripd = avaliar_ripd(op)
    print(
        _dump(
            {
                "operacao": ripd.operacao,
                "score": ripd.score,
                "nivel": ripd.nivel,
                "conforme": ripd.conforme,
                "riscos": [
                    {
                        "descricao": r.descricao,
                        "severidade": r.severidade,
                        "recomendacao": r.recomendacao,
                        "artigo": r.artigo,
                    }
                    for r in ripd.riscos
                ],
            }
        )
    )
    return 0


def cmd_dpa(args: argparse.Namespace) -> int:
    """Renderiza um DPA (Acordo de Tratamento de Dados — Art. 39)."""
    cats = tuple(c.strip() for c in (args.categorias or "").split(",") if c.strip())
    params = DPAParams(
        controlador=args.controlador,
        operador=args.operador,
        objeto=args.objeto or "",
        finalidade=args.finalidade,
        categorias_dados=cats,
        prazo_retencao=args.prazo_retencao or "",
        suboperadores_permitidos=args.suboperadores,
        transferencia_internacional=args.transferencia_internacional,
    )
    print(_dump({"dpa": render_dpa(params)}))
    return 0


def cmd_anpd(args: argparse.Namespace) -> int:
    """Gera plano de resposta a incidente (ANPD — Art. 48 LGPD)."""
    dados = tuple(TipoDado(t) for t in (args.dados_afetados or []))
    descricao = _make_redactor().redact(args.descricao).redacted_text
    data_desc = date.fromisoformat(args.data_descoberta) if args.data_descoberta else date.today()
    hoje = date.fromisoformat(args.hoje) if args.hoje else None
    inc = Incidente(
        incidente_id=args.incidente_id,
        descricao=descricao,
        data_descoberta=data_desc,
        dados_afetados=dados,
        num_titulares=args.num_titulares,
        vazamento_confirmado=args.vazamento_confirmado,
    )
    plano = gerar_plano(inc, hoje=hoje)
    print(
        _dump(
            {
                "incidente_id": plano.incidente_id,
                "severidade": plano.severidade,
                "comunicar_anpd": plano.comunicar_anpd,
                "comunicar_titulares": plano.comunicar_titulares,
                "prazo_anpd": plano.prazo_anpd.isoformat() if plano.prazo_anpd else None,
                "dias_restantes": plano.dias_restantes,
                "passos": list(plano.passos),
            }
        )
    )
    return 0


def cmd_doc_template(args: argparse.Namespace) -> int:
    """Renderiza um template juridico (procuracao | contrato_honorarios)."""
    vars_raw = args.vars or "{}"
    try:
        data = json.loads(vars_raw)
    except json.JSONDecodeError as e:
        print(_dump({"error": f"vars JSON invalido: {e}"}))
        return 2
    if not isinstance(data, dict):
        print(_dump({"error": "vars deve ser um objeto JSON"}))
        return 2

    if args.template == "procuracao":
        campos = ProcuracaoCampos(
            outorgante=data.get("outorgante"),
            outorgado=data.get("outorgado"),
            oab=data.get("oab"),
            poderes=data.get("poderes", "desconhecido"),
            comarca=data.get("comarca"),
            data=date.fromisoformat(data["data"]) if data.get("data") else None,
        )
        texto = render_procuracao(campos)
    else:
        chon = ContratoHonorariosCampos(
            contratante=data.get("contratante"),
            contratado=data.get("contratado"),
            objeto=data.get("objeto"),
            valor=data.get("valor"),
            percentual=data.get("percentual"),
            forma_pagamento=data.get("forma_pagamento", "desconhecido"),
            foro_eleicao=data.get("foro_eleicao"),
        )
        texto = render_contrato_honorarios(chon)
    print(_dump({"template": args.template, "texto": texto}))
    return 0


def cmd_doc_extract(args: argparse.Namespace) -> int:
    """Extrai campos estruturados de procuracao ou contrato de honorarios."""
    text = _read_input(args.input)
    if args.kind == "procuracao":
        c = extract_procuracao(text)
        out = {
            "outorgante": c.outorgante,
            "outorgado": c.outorgado,
            "oab": c.oab,
            "poderes": c.poderes,
            "comarca": c.comarca,
            "data": c.data.isoformat() if c.data else None,
            "campos_ausentes": list(c.campos_ausentes),
            "confianca": c.confianca,
        }
    else:
        ch = extract_contrato_honorarios(text)
        out = {
            "contratante": ch.contratante,
            "contratado": ch.contratado,
            "objeto": ch.objeto,
            "valor": ch.valor,
            "percentual": ch.percentual,
            "forma_pagamento": ch.forma_pagamento,
            "foro_eleicao": ch.foro_eleicao,
            "campos_ausentes": list(ch.campos_ausentes),
            "confianca": ch.confianca,
        }
    print(_dump({"kind": args.kind, "campos": out}))
    return 0


_SOCIO_TIPOS = ("administrador", "quotista", "acionista")
_SOC_TIPOS = (
    "ltda",
    "sa_fechada",
    "sa_aberta",
    "eireli",
    "mei",
    "slu",
    "desconhecido",
)


def cmd_societario(args: argparse.Namespace) -> int:
    """Valida coerencia de participacoes societarias (CC/2002).

    Constroi ``EstruturaSocietaria`` a partir de ``--socios`` (JSON: lista de
    objetos {nome_alias, percentual, tipo}) e chama ``validar_participacoes``.
    """
    try:
        raw = json.loads(args.socios)
    except json.JSONDecodeError as e:
        print(_dump({"error": f"socios JSON invalido: {e}"}))
        return 2
    if not isinstance(raw, list):
        print(_dump({"error": "socios deve ser uma lista JSON"}))
        return 2

    socios: list[Socio] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            print(_dump({"error": f"socio[{idx}] deve ser objeto JSON"}))
            return 2
        tipo = entry.get("tipo", "quotista")
        if tipo not in _SOCIO_TIPOS:
            print(
                _dump(
                    {
                        "error": f"socio[{idx}].tipo invalido: {tipo!r}",
                        "tipos": list(_SOCIO_TIPOS),
                    }
                )
            )
            return 2
        try:
            pct = float(entry["percentual"])
        except (KeyError, TypeError, ValueError):
            print(_dump({"error": f"socio[{idx}].percentual ausente ou nao numerico"}))
            return 2
        socios.append(
            Socio(
                nome=str(entry.get("nome_alias", f"socio-{idx}")),
                participacao_pct=pct,
                tipo=tipo,
            )
        )

    estrutura = EstruturaSocietaria(
        tipo=args.tipo,
        cnpj=args.cnpj,
        socios=tuple(socios),
        capital_social=args.capital_social,
    )
    problemas = validar_participacoes(estrutura)
    print(
        _dump(
            {
                "tipo": estrutura.tipo,
                "cnpj": estrutura.cnpj,
                "n_socios": len(socios),
                "soma_participacoes": sum(s.participacao_pct for s in socios),
                "coerente": not problemas,
                "problemas": list(problemas),
            }
        )
    )
    return 0 if not problemas else 1


def cmd_vendor_review(args: argparse.Namespace) -> int:
    """Emite o checklist padrao de review de fornecedor de IA (LGPD).

    A API (`checklist_vendor_padrao`) nao recebe vendor/finalidade — expoe o
    checklist padrao estruturado para preenchimento downstream.
    """
    review = checklist_vendor_padrao()
    payload = {
        "checklist": "vendor_ai_review_padrao",
        "nota": "API nao recebe vendor/finalidade; emite checklist padrao.",
        "score": review.score(),
        "aprovado": review.aprovado(),
        "itens": [
            {
                "chave": it.chave,
                "pergunta": it.pergunta,
                "artigo": it.artigo,
                "status": it.status,
                "obrigatorio": it.obrigatorio,
            }
            for it in review.itens
        ],
    }
    if args.format == "json":
        print(_dump(payload))
    else:
        print(f"checklist: {payload['checklist']} ({len(review.itens)} itens)")
        for it in review.itens:
            mark = "*" if it.obrigatorio else " "
            print(f"  [{mark}] {it.chave} ({it.artigo}): {it.pergunta}")
    return 0


def cmd_disclosure(args: argparse.Namespace) -> int:
    """Cruza representacoes x disclosure schedule (gaps + inconsistencias).

    ``--representacoes`` JSON: lista de {id, texto, requer_schedule}.
    ``--schedule`` JSON: lista de {rep_id, conteudo}.
    """
    try:
        reps_raw = json.loads(args.representacoes)
    except json.JSONDecodeError as e:
        print(_dump({"error": f"representacoes JSON invalido: {e}"}))
        return 2
    if not isinstance(reps_raw, list):
        print(_dump({"error": "representacoes deve ser uma lista JSON"}))
        return 2

    try:
        sched_raw = json.loads(args.schedule) if args.schedule else []
    except json.JSONDecodeError as e:
        print(_dump({"error": f"schedule JSON invalido: {e}"}))
        return 2
    if not isinstance(sched_raw, list):
        print(_dump({"error": "schedule deve ser uma lista JSON"}))
        return 2

    reps: list[Representacao] = []
    for idx, entry in enumerate(reps_raw):
        if not isinstance(entry, dict) or "id" not in entry:
            print(_dump({"error": f"representacao[{idx}] precisa de objeto com 'id'"}))
            return 2
        reps.append(
            Representacao(
                id=str(entry["id"]),
                texto=str(entry.get("texto", "")),
                requer_schedule=bool(entry.get("requer_schedule", True)),
            )
        )

    items: list[DisclosureItem] = []
    for idx, entry in enumerate(sched_raw):
        if not isinstance(entry, dict) or "rep_id" not in entry:
            print(_dump({"error": f"schedule[{idx}] precisa de objeto com 'rep_id'"}))
            return 2
        items.append(
            DisclosureItem(
                rep_id=str(entry["rep_id"]),
                conteudo=str(entry.get("conteudo", "")),
            )
        )

    schedule = DisclosureSchedule(items)
    gaps = find_gaps(tuple(reps), schedule)
    inc = inconsistencias(tuple(reps), schedule)
    print(
        _dump(
            {
                "n_representacoes": len(reps),
                "n_schedule_items": len(items),
                "gaps": [{"id": r.id, "texto": r.texto} for r in gaps],
                "inconsistencias": [{"rep_id": i.rep_id, "conteudo": i.conteudo} for i in inc],
            }
        )
    )
    return 0 if not gaps and not inc else 1


def cmd_due_diligence(args: argparse.Namespace) -> int:
    """Emite o checklist padrao de due diligence BR (opcional filtro por area).

    A API (`checklist_padrao`) nao recebe input; ``--area`` filtra os itens
    emitidos no adapter.
    """
    checklist = checklist_padrao()
    itens = checklist.itens
    if args.area:
        itens = tuple(it for it in itens if it.area == args.area)
    print(
        _dump(
            {
                "checklist": "due_diligence_padrao",
                "area_filtro": args.area,
                "n_itens": len(itens),
                "score": checklist.score(),
                "itens": [
                    {
                        "area": it.area,
                        "descricao": it.descricao,
                        "obrigatorio": it.obrigatorio,
                        "referencia": it.referencia,
                        "status": it.status,
                    }
                    for it in itens
                ],
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
    p_redact.add_argument(
        "--strict",
        action="store_true",
        help="Falha com exit 3 se sobrar PII estruturada apos redacao",
    )
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

    p_dsar = sub.add_parser("dsar", help="Processa requisicao de titular (Art. 18 LGPD)")
    p_dsar.add_argument("--input", "-i", help="Texto da requisicao (default: stdin)")
    p_dsar.add_argument(
        "--direito",
        default=None,
        help="Codigo do direito (Art. 18); se omitido, classifica do texto",
    )
    p_dsar.add_argument("--request-id", default="req-1", help="ID opaco da requisicao")
    p_dsar.add_argument(
        "--titular-ref",
        default="titular-anon",
        help="Pseudonimo opaco do titular (NUNCA PII real)",
    )
    p_dsar.add_argument("--recebimento", help="Data recebimento ISO (default: hoje)")
    p_dsar.add_argument("--hoje", help="Data atual ISO (default: hoje)")
    p_dsar.add_argument(
        "--skip-redact",
        action="store_true",
        help="Pula redacao de PII (use so se texto ja redigido)",
    )
    p_dsar.set_defaults(func=cmd_dsar)

    p_prazo = sub.add_parser("prazo", help="Calcula prazo CPC deterministico")
    p_prazo.add_argument("--data-publicacao", required=True, help="Data publicacao/intimacao ISO")
    p_prazo.add_argument("--prazo-dias", type=int, required=True, help="Prazo base em dias")
    p_prazo.add_argument(
        "--parte",
        choices=["particular", "fazenda", "mp", "defensoria"],
        default="particular",
        help="Tipo de parte para eventual prazo em dobro",
    )
    p_prazo.add_argument("--via-dje", action="store_true", help="Intimacao via DJE")
    p_prazo.add_argument("--tribunal", default="TJPR", help="Tribunal (default TJPR)")
    p_prazo.add_argument("--hoje", help="Data atual ISO (default: hoje)")
    p_prazo.add_argument("--salvar", action="store_true", help="Registra prazo em data/prazos.json")
    p_prazo.add_argument("--ref", help="Referencia opaca do processo/caso (ex: PROC-001)")
    p_prazo.add_argument("--ato", help="Descricao curta do ato/prazo")
    p_prazo.set_defaults(func=cmd_prazo)

    p_val = sub.add_parser(
        "validar-extracao",
        help="Oracle: valida duas extrações de intimação (dual-model) antes do cálculo",
    )
    p_val.add_argument("--file-a", required=True, help="JSON da extração do modelo A")
    p_val.add_argument("--file-b", required=True, help="JSON da extração do modelo B")
    p_val.add_argument("--hoje", help="Data atual ISO (default: hoje)")
    p_val.set_defaults(func=cmd_validar_extracao)

    p_calc = sub.add_parser(
        "calc-disponivel",
        help="Preflight fail-closed: prova que o motor de cálculo está são",
    )
    p_calc.set_defaults(func=cmd_calc_disponivel)

    p_scan = sub.add_parser("scan-state", help="Estado da ultima varredura de caixa")
    p_scan.add_argument("--get", action="store_true", help="Imprime o estado descrito")
    p_scan.add_argument("--set", action="store_true", help="Grava resultado da varredura")
    p_scan.add_argument(
        "--resultado",
        choices=["ok", "vazio", "falha"],
        default="vazio",
        help="Resultado da varredura (com --set)",
    )
    p_scan.add_argument("--quando", help="Timestamp ISO da varredura (com --set)")
    p_scan.add_argument("--n-encontrados", type=int, default=0)
    p_scan.add_argument("--n-processados", type=int, default=0)
    p_scan.add_argument("--n-revisao", type=int, default=0)
    p_scan.add_argument("--hoje", help="Data atual ISO (com --get)")
    p_scan.set_defaults(func=cmd_scan_state)

    p_tri = sub.add_parser("triagem", help="Filtra candidatos de tribunal de uma lista de emails")
    p_tri.add_argument("--input", required=True, help="JSON: lista de {sender,subject,data,body}")
    p_tri.add_argument("--janela", type=int, default=7, help="Janela em dias corridos")
    p_tri.add_argument("--hoje", help="Data atual ISO (default: hoje)")
    p_tri.set_defaults(func=cmd_triagem)

    p_prazos = sub.add_parser("prazos", help="Lista prazos locais registrados")
    p_prazos.add_argument("--ate", type=int, default=7, help="Janela em dias corridos (default 7)")
    p_prazos.add_argument(
        "--incluir-cumpridos",
        action="store_true",
        help="Inclui registros com status cumprido",
    )
    p_prazos.add_argument("--hoje", help="Data atual ISO (default: hoje)")
    p_prazos.set_defaults(func=cmd_prazos)

    p_hon = sub.add_parser("honorarios", help="Registra/lista honorarios locais por alias")
    hon_mode = p_hon.add_mutually_exclusive_group(required=True)
    hon_mode.add_argument("--add", action="store_true", help="Adiciona item ao ledger")
    hon_mode.add_argument("--list", action="store_true", help="Lista itens do ledger")
    p_hon.add_argument("--ref", help="Referencia alias-only (ex: CLI-001)")
    p_hon.add_argument("--descricao", help="Descricao curta sem nome real")
    p_hon.add_argument("--valor", type=float, help="Valor em reais")
    p_hon.add_argument("--data", help="Data ISO AAAA-MM-DD")
    p_hon.add_argument(
        "--status",
        choices=["pendente", "pago"],
        default="pendente",
        help="Status do item (default pendente)",
    )
    p_hon.set_defaults(func=cmd_honorarios)

    p_cli = sub.add_parser("clientes", help="Registra/lista metadados alias-only de clientes")
    cli_mode = p_cli.add_mutually_exclusive_group(required=True)
    cli_mode.add_argument("--add", action="store_true", help="Adiciona alias ao registro")
    cli_mode.add_argument("--list", action="store_true", help="Lista aliases registrados")
    p_cli.add_argument("--alias", help="Alias sem nome real (ex: CLI-001)")
    p_cli.add_argument("--area", help="Area de pratica/metadado do alias")
    p_cli.add_argument("--tribunal", help="Tribunal principal/metadado do alias")
    p_cli.add_argument("--obs", default="", help="Observacao sem PII/nome real")
    p_cli.set_defaults(func=cmd_clientes)

    p_ren = sub.add_parser("renovacao", help="Lista alertas de renovacao de contratos")
    p_ren.add_argument("--hoje", help="Data atual ISO (default: hoje)")
    p_ren.add_argument("--incluir-ok", action="store_true", help="Inclui contratos com status ok")
    p_ren.set_defaults(func=cmd_renovacao)

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

    # ── v0.2 bridges: deterministic internal modules → CLI subcommands ──
    _tipos = [t.value for t in TipoDado]
    _bases = [b.value for b in BaseLegal]

    p_trib = sub.add_parser("tribunal-detect", help="Detecta tribunal por sender + corpo")
    p_trib.add_argument("--input", "-i", help="Texto (default: stdin)")
    p_trib.add_argument("--sender", default="", help="From: header (ex: x@tjpr.jus.br)")
    p_trib.set_defaults(func=cmd_tribunal_detect)

    p_rf = sub.add_parser("red-flags", help="Scan red flags em contrato de aquisicao")
    p_rf.add_argument("--input", "-i", help="Texto (default: stdin)")
    p_rf.add_argument("--skip-redact", action="store_true", help="Pula redacao (ja redigido)")
    p_rf.set_defaults(func=cmd_red_flags)

    p_pia = sub.add_parser("pia", help="Avalia RIPD/PIA de uma operacao de tratamento")
    p_pia.add_argument("--tipo-operacao", required=True, help="Ex: coleta, compartilhamento")
    p_pia.add_argument("--finalidade", required=True, help="Finalidade do tratamento")
    p_pia.add_argument("--base-legal", choices=_bases, default="legitimo_interesse")
    p_pia.add_argument(
        "--tipos-dados",
        nargs="*",
        choices=_tipos,
        default=[],
        help="Categorias de dados (comum/sensivel/crianca)",
    )
    p_pia.add_argument("--nao-necessario", action="store_true", help="Marca necessario=False")
    p_pia.set_defaults(func=cmd_pia)

    p_dpa = sub.add_parser("dpa", help="Renderiza DPA (Art. 39)")
    p_dpa.add_argument("--controlador", required=True)
    p_dpa.add_argument("--operador", required=True)
    p_dpa.add_argument("--finalidade", required=True)
    p_dpa.add_argument("--objeto", default="")
    p_dpa.add_argument("--categorias", default="", help="Lista separada por virgula")
    p_dpa.add_argument("--prazo-retencao", default="")
    p_dpa.add_argument("--suboperadores", action="store_true")
    p_dpa.add_argument("--transferencia-internacional", action="store_true")
    p_dpa.set_defaults(func=cmd_dpa)

    p_anpd = sub.add_parser("anpd", help="Gera plano de resposta a incidente (Art. 48)")
    p_anpd.add_argument("--incidente-id", default="inc-1")
    p_anpd.add_argument("--descricao", required=True, help="Descricao (sera redigida)")
    p_anpd.add_argument("--data-descoberta", help="ISO (default: hoje)")
    p_anpd.add_argument("--dados-afetados", nargs="*", choices=_tipos, default=[])
    p_anpd.add_argument("--num-titulares", type=int, default=0)
    p_anpd.add_argument("--vazamento-confirmado", action="store_true")
    p_anpd.add_argument("--hoje", help="Data atual ISO")
    p_anpd.set_defaults(func=cmd_anpd)

    p_doctpl = sub.add_parser("doc-template", help="Renderiza template juridico")
    p_doctpl.add_argument(
        "--template",
        choices=["procuracao", "contrato_honorarios"],
        required=True,
    )
    p_doctpl.add_argument("--vars", default="{}", help="Variaveis JSON")
    p_doctpl.set_defaults(func=cmd_doc_template)

    p_dext = sub.add_parser("doc-extract", help="Extrai campos de procuracao/contrato")
    p_dext.add_argument("--input", "-i", help="Texto (default: stdin)")
    p_dext.add_argument(
        "--kind",
        choices=["procuracao", "contrato_honorarios"],
        default="procuracao",
    )
    p_dext.set_defaults(func=cmd_doc_extract)

    # ── v0.3 bridges: M&A / societario internal modules → CLI subcommands ──
    p_soc = sub.add_parser(
        "societario", help="Valida coerencia de participacoes societarias (CC/2002)"
    )
    p_soc.add_argument(
        "--socios",
        required=True,
        help="JSON: lista de {nome_alias, percentual, tipo}. tipo in "
        "administrador|quotista|acionista",
    )
    p_soc.add_argument("--tipo", choices=list(_SOC_TIPOS), default="ltda")
    p_soc.add_argument("--cnpj", default=None, help="CNPJ (digitos ou formatado)")
    p_soc.add_argument("--capital-social", type=float, default=None)
    p_soc.set_defaults(func=cmd_societario)

    p_vr = sub.add_parser(
        "vendor-review",
        help="Emite checklist padrao de review de fornecedor de IA (API nao recebe "
        "vendor/finalidade)",
    )
    p_vr.add_argument("--format", choices=["json", "text"], default="json")
    p_vr.set_defaults(func=cmd_vendor_review)

    p_disc = sub.add_parser(
        "disclosure", help="Cruza representacoes x disclosure schedule (gaps/inconsistencias)"
    )
    p_disc.add_argument(
        "--representacoes",
        required=True,
        help="JSON: lista de {id, texto, requer_schedule}",
    )
    p_disc.add_argument(
        "--schedule",
        default=None,
        help="JSON: lista de {rep_id, conteudo} (default: vazio)",
    )
    p_disc.set_defaults(func=cmd_disclosure)

    p_dd = sub.add_parser(
        "due-diligence", help="Emite checklist padrao de due diligence BR (filtro por --area)"
    )
    p_dd.add_argument(
        "--area",
        choices=["trabalhista", "fiscal", "ambiental", "contratual", "societario"],
        default=None,
        help="Filtra itens por area (default: todas)",
    )
    p_dd.set_defaults(func=cmd_due_diligence)

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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _apply_config_defaults(args)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
