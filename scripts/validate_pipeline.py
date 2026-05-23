"""Validacao end-to-end do pipeline LegalOps BR.

Roda emails sinteticos pelo pipeline completo:
    Email TJPR -> pii_redactor -> tjpr_parser -> cpc_prazos

Saida: metrics/pipeline_validation_YYYYMMDD.json + print stdout.

Uso:
    uv run python scripts/validate_pipeline.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legalops.cpc_prazos import PrazoInput, calcular_prazo  # noqa: E402
from legalops.pii_redactor import PIIRedactor  # noqa: E402
from legalops.tjpr_parser import parse_email  # noqa: E402

OUT_DIR = Path(__file__).parent.parent / "metrics"


SYNTHETIC_EMAILS = [
    {
        "idx": 0,
        "descricao": "Despacho simples com prazo 15 dias",
        "text": (
            "De: projudisistema@tjpr.jus.br\n"
            "Data: 21/05/2026\n"
            "Comarca de Curitiba\n"
            "Processo 0001234-56.2026.8.16.0001\n"
            "Procurador OAB/PR 12345 (CPF 123.456.789-00)\n"
            "Despacho: Intime-se a parte re para contestar no prazo de 15 dias uteis.\n"
        ),
    },
    {
        "idx": 1,
        "descricao": "Sentenca contra Fazenda (dobro)",
        "text": (
            "De: projudisistema@tjpr.jus.br\n"
            "Data: 15/06/2026\n"
            "Vara da Fazenda Publica de Curitiba\n"
            "Processo 0005678-90.2026.8.16.0002\n"
            "Sentenca: julgo procedente em parte. Recorrer no prazo de 15 dias.\n"
            "Reclamado: Municipio de Curitiba (CNPJ 76.417.005/0001-86)\n"
        ),
    },
    {
        "idx": 2,
        "descricao": "Multiplos processos no mesmo email",
        "text": (
            "De: projudisistema@tjpr.jus.br\n"
            "Data: 22/05/2026\n"
            "Processo 0009999-11.2026.8.16.0001\n"
            "Despacho: prazo de 5 dias.\n"
            "===\n"
            "Processo 0008888-22.2026.8.16.0002\n"
            "Decisao: agravo no prazo de 15 dias.\n"
        ),
    },
    {
        "idx": 3,
        "descricao": "Email sem processo (deve falhar gracefully)",
        "text": (
            "Email comum sem numero de processo. "
            "Talvez seja spam ou notificacao administrativa."
        ),
    },
]


def run_pipeline(email_text: str, hoje: date) -> dict[str, object]:
    """Executa pipeline em 1 email."""
    redactor = PIIRedactor()

    redacted = redactor.redact(email_text)
    parse_result = parse_email(redacted.redacted_text)

    prazos: list[dict[str, object]] = []
    for intim in parse_result.intimacoes:
        if intim.prazo_dias is None or intim.data_publicacao is None:
            continue
        try:
            res = calcular_prazo(
                PrazoInput(
                    data_publicacao=intim.data_publicacao,
                    prazo_dias=intim.prazo_dias,
                    parte="particular",
                ),
                hoje=hoje,
            )
            prazos.append(
                {
                    "processo": intim.numero_processo,
                    "dies_a_quo": res.dies_a_quo.isoformat(),
                    "dies_ad_quem": res.dies_ad_quem.isoformat(),
                    "alerta": res.alerta,
                }
            )
        except Exception as e:  # noqa: BLE001
            prazos.append({"processo": intim.numero_processo, "erro": str(e)})

    sucesso = parse_result.total > 0 or not redacted.has_pii
    return {
        "redacted_chars": len(redacted.redacted_text),
        "pii_redacted": len(redacted.matches),
        "intimacoes_found": parse_result.total,
        "prazos_calculados": prazos,
        "parser_errors": parse_result.erros,
        "sucesso": sucesso,
    }


def main() -> int:
    hoje = date(2026, 5, 22)
    results: list[dict[str, object]] = []
    falhas: list[str] = []

    for email in SYNTHETIC_EMAILS:
        try:
            r = run_pipeline(str(email["text"]), hoje=hoje)
            r["idx"] = email["idx"]
            r["descricao"] = email["descricao"]
            results.append(r)
            if not r["sucesso"]:
                falhas.append(f"#{email['idx']}: {email['descricao']}")
        except Exception as e:  # noqa: BLE001
            results.append(
                {
                    "idx": email["idx"],
                    "descricao": email["descricao"],
                    "erro": str(e),
                    "sucesso": False,
                }
            )
            falhas.append(f"#{email['idx']}: EXCEPTION {e}")

    total_sucesso = sum(1 for r in results if r.get("sucesso"))

    metrics = {
        "tested_at": dt.datetime.now(dt.UTC).isoformat(),
        "n_emails": len(SYNTHETIC_EMAILS),
        "total_sucesso": total_sucesso,
        "falhas": falhas,
        "results": results,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    out_path = OUT_DIR / f"pipeline_validation_{today}.json"
    out_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))

    print("\n=== Pipeline Validation ===")
    print(f"Emails testados:     {len(SYNTHETIC_EMAILS)}")
    print(f"Sucesso:             {total_sucesso}/{len(SYNTHETIC_EMAILS)}")
    if falhas:
        print("Falhas:")
        for f in falhas:
            print(f"  - {f}")
    print(f"\nDetalhes em:         {out_path}")

    for r in results:
        idx = r.get("idx")
        desc = r.get("descricao")
        intim = r.get("intimacoes_found", "?")
        pii = r.get("pii_redacted", "?")
        prazos = r.get("prazos_calculados", [])
        n_prazos = len(prazos) if isinstance(prazos, list) else 0
        print(f"  #{idx} '{desc}': pii={pii}, intim={intim}, prazos={n_prazos}")

    if total_sucesso < len(SYNTHETIC_EMAILS) - 1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
