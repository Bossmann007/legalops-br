"""Validacao end-to-end do pipeline LegalOps BR.

Roda emails sinteticos pelo orchestrator (mesmo codigo de producao).
Cada caso especifica `parte` para exercitar dobro Fazenda/MP/Defensoria.

Saida: metrics/pipeline_validation_YYYYMMDD.json + print stdout.
Exit 0 se todos casos OK, 1 senao.

Uso:
    uv run python scripts/validate_pipeline.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from datetime import date
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legalops.orchestrator import ProcessedIntimacao, process_email  # noqa: E402

OUT_DIR = Path(__file__).parent.parent / "metrics"

ParteType = Literal["particular", "fazenda", "mp", "defensoria"]


SYNTHETIC_CASES: list[dict[str, object]] = [
    {
        "idx": 0,
        "descricao": "Despacho particular prazo 15 dias",
        "parte": "particular",
        "via_dje": False,
        "text": (
            "De: projudisistema@tjpr.jus.br\n"
            "Data: 21/05/2026\n"
            "Comarca de Curitiba\n"
            "Processo 0001234-56.2026.8.16.0001\n"
            "Procurador OAB/PR 12345 (CPF 123.456.789-00)\n"
            "Despacho: Intime-se a parte re para contestar no prazo de 15 dias uteis.\n"
        ),
        "expected_prazo_efetivo_dias": 15,
    },
    {
        "idx": 1,
        "descricao": "Sentenca contra Fazenda (dobro Art. 183)",
        "parte": "fazenda",
        "via_dje": False,
        "text": (
            "De: projudisistema@tjpr.jus.br\n"
            "Data: 15/06/2026\n"
            "Vara da Fazenda Publica de Curitiba\n"
            "Processo 0005678-90.2026.8.16.0002\n"
            "Sentenca: julgo procedente em parte. Recorrer no prazo de 15 dias.\n"
            "Reclamado: Municipio de Curitiba (CNPJ 76.417.005/0001-86)\n"
        ),
        "expected_prazo_efetivo_dias": 30,
    },
    {
        "idx": 2,
        "descricao": "Multiplos processos no mesmo email",
        "parte": "particular",
        "via_dje": False,
        "text": (
            "De: projudisistema@tjpr.jus.br\n"
            "Data: 22/05/2026\n"
            "Processo 0009999-11.2026.8.16.0001\n"
            "Despacho: prazo de 5 dias.\n"
            "===\n"
            "Processo 0008888-22.2026.8.16.0002\n"
            "Decisao: agravo no prazo de 15 dias.\n"
        ),
        "expected_intimacoes": 2,
    },
    {
        "idx": 3,
        "descricao": "Intimacao via DJE pula um dia util (Art. 231 #1)",
        "parte": "particular",
        "via_dje": True,
        "text": (
            "De: projudisistema@tjpr.jus.br\n"
            "Data: 21/05/2026\n"
            "Processo 0007777-77.2026.8.16.0001\n"
            "Despacho: prazo de 15 dias uteis.\n"
        ),
        "expected_prazo_efetivo_dias": 15,
    },
    {
        "idx": 4,
        "descricao": "Email sem processo (deve retornar lista vazia)",
        "parte": "particular",
        "via_dje": False,
        "text": "Email comum sem numero de processo.",
        "expected_intimacoes": 0,
    },
]


def _validate_case(
    case: dict[str, object], results: list[ProcessedIntimacao]
) -> tuple[bool, list[str]]:
    """Valida um caso contra expectations. Retorna (ok, erros)."""
    erros: list[str] = []

    if "expected_intimacoes" in case:
        expected = int(case["expected_intimacoes"])  # type: ignore[arg-type]
        if len(results) != expected:
            erros.append(f"intimacoes={len(results)} esperado={expected}")

    if "expected_prazo_efetivo_dias" in case and results:
        expected = int(case["expected_prazo_efetivo_dias"])  # type: ignore[arg-type]
        prazo = results[0].prazo
        if prazo is None:
            erros.append("prazo None inesperado")
        elif prazo.prazo_efetivo_dias != expected:
            erros.append(
                f"prazo_efetivo_dias={prazo.prazo_efetivo_dias} esperado={expected}"
            )

    return not erros, erros


def main() -> int:
    hoje = date(2026, 5, 22)
    results_out: list[dict[str, object]] = []
    falhas: list[str] = []

    for case in SYNTHETIC_CASES:
        try:
            processed = process_email(
                str(case["text"]),
                parte=str(case["parte"]),  # type: ignore[arg-type]
                via_dje=bool(case["via_dje"]),
                hoje=hoje,
            )
            ok, erros_caso = _validate_case(case, processed)

            results_out.append(
                {
                    "idx": case["idx"],
                    "descricao": case["descricao"],
                    "parte": case["parte"],
                    "via_dje": case["via_dje"],
                    "n_intimacoes": len(processed),
                    "prazos": [
                        {
                            "numero_processo": r.numero_processo,
                            "prazo_efetivo_dias": r.prazo.prazo_efetivo_dias
                            if r.prazo
                            else None,
                            "dies_a_quo": r.prazo.dies_a_quo.isoformat()
                            if r.prazo
                            else None,
                            "dies_ad_quem": r.prazo.dies_ad_quem.isoformat()
                            if r.prazo
                            else None,
                            "alerta": r.prazo.alerta if r.prazo else None,
                        }
                        for r in processed
                    ],
                    "ok": ok,
                    "erros": erros_caso,
                }
            )
            if not ok:
                falhas.append(f"#{case['idx']}: {erros_caso}")
        except Exception as e:  # noqa: BLE001
            results_out.append(
                {
                    "idx": case["idx"],
                    "descricao": case["descricao"],
                    "ok": False,
                    "erros": [f"EXCEPTION: {e}"],
                }
            )
            falhas.append(f"#{case['idx']}: EXCEPTION {e}")

    total_ok = sum(1 for r in results_out if r.get("ok"))

    metrics = {
        "tested_at": dt.datetime.now(dt.UTC).isoformat(),
        "n_cases": len(SYNTHETIC_CASES),
        "total_ok": total_ok,
        "falhas": falhas,
        "results": results_out,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    out_path = OUT_DIR / f"pipeline_validation_{today}.json"
    out_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))

    print("\n=== Pipeline Validation ===")
    print(f"Casos testados:      {len(SYNTHETIC_CASES)}")
    print(f"OK:                  {total_ok}/{len(SYNTHETIC_CASES)}")
    if falhas:
        print("Falhas:")
        for f in falhas:
            print(f"  - {f}")
    print(f"\nDetalhes em:         {out_path}")

    return 0 if total_ok == len(SYNTHETIC_CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
