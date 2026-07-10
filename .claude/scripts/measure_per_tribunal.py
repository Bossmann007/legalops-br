"""Mede metricas de parsers POR TRIBUNAL no corpus sintetico.

Uso:
    uv run python scripts/measure_per_tribunal.py [--corpus DIR] [--out DIR]

Para cada doc:
- routing: detect_tribunal deve retornar o tribunal esperado (sender sintetico)
- parsing: orchestrator.process_email roda o pipeline completo
- agrega por tribunal: n_docs, n_intimacoes_detected, parsers_routing_accuracy,
  prazo_extraction_rate

Saida: metrics/per_tribunal_YYYYMMDD.json + tabela stdout.
Exit 0 se todos tribunais (com >=1 doc) tiverem prazo_extraction_rate >= 0.80.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legalops.orchestrator import process_email  # noqa: E402
from legalops.tribunal_detector import detect_tribunal  # noqa: E402

DEFAULT_CORPUS = Path(__file__).parent.parent / "corpus" / "synthetic" / "docs"
DEFAULT_OUT = Path(__file__).parent.parent / "metrics"

# Tribunais com parser real no orchestrator (skip 'neutro' e ausentes do detector)
ROUTABLE = {"tjpr", "tjsp", "tjsc", "tjrj"}
SENDER_BY_TRIBUNAL = {
    "tjpr": "noreply@tjpr.jus.br",
    "tjsp": "noreply@tjsp.jus.br",
    "tjsc": "noreply@tjsc.jus.br",
    "tjrj": "noreply@tjrj.jus.br",
    "tjdft": "noreply@tjdft.jus.br",
    "tjmg": "noreply@tjmg.jus.br",
    "neutro": "",
}

PRAZO_THRESHOLD = 0.80


def load_corpus(corpus_dir: Path) -> list[dict[str, Any]]:
    return [json.loads(p.read_text()) for p in sorted(corpus_dir.glob("doc_*.json"))]


def aggregate(docs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Agrupa por tribunal e mede routing + prazo extraction."""
    by_tribunal: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n_docs": 0,
            "n_intimacoes_detected": 0,
            "n_routing_correct": 0,
            "n_with_expected_prazo": 0,
            "n_prazo_extracted": 0,
        }
    )

    for doc in docs:
        tribunal = str(doc.get("tribunal", "neutro"))
        text = str(doc["text"])
        sender = SENDER_BY_TRIBUNAL.get(tribunal, "")

        bucket = by_tribunal[tribunal]
        bucket["n_docs"] += 1

        detected = detect_tribunal(text, sender=sender)
        expected_routing = tribunal if tribunal in ROUTABLE else "unknown"
        if detected == expected_routing or (tribunal == "neutro" and detected == "unknown"):
            bucket["n_routing_correct"] += 1

        # Heuristica: doc tem prazo esperado se template contem "prazo" ou "dias"
        text_lower = text.lower()
        has_expected_prazo = "prazo" in text_lower or "dias" in text_lower
        if has_expected_prazo:
            bucket["n_with_expected_prazo"] += 1

        try:
            results = process_email(text, sender=sender)
        except (ValueError, KeyError, AttributeError) as e:
            bucket.setdefault("errors", []).append(str(e))
            continue

        bucket["n_intimacoes_detected"] += len(results)
        if has_expected_prazo and any(r.parsed.prazo_dias is not None for r in results):
            bucket["n_prazo_extracted"] += 1

    out: dict[str, dict[str, Any]] = {}
    for trib, b in by_tribunal.items():
        n = b["n_docs"]
        n_exp = b["n_with_expected_prazo"]
        out[trib] = {
            "n_docs": n,
            "n_intimacoes_detected": b["n_intimacoes_detected"],
            "parsers_routing_accuracy": round(b["n_routing_correct"] / n, 4) if n else 0.0,
            "prazo_extraction_rate": round(b["n_prazo_extracted"] / n_exp, 4) if n_exp else 0.0,
            "n_with_expected_prazo": n_exp,
            "n_prazo_extracted": b["n_prazo_extracted"],
        }
    return out


def print_table(per_tribunal: dict[str, dict[str, Any]]) -> None:
    print("\n=== Per-Tribunal Metrics ===")
    header = f"{'tribunal':<10} {'n_docs':>7} {'intim':>7} {'routing':>9} {'prazo':>8}"
    print(header)
    print("-" * len(header))
    for trib in sorted(per_tribunal):
        m = per_tribunal[trib]
        print(
            f"{trib:<10} {m['n_docs']:>7} {m['n_intimacoes_detected']:>7} "
            f"{m['parsers_routing_accuracy']:>9.2%} {m['prazo_extraction_rate']:>8.2%}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.corpus.exists():
        print(f"ERRO: corpus nao existe em {args.corpus}", file=sys.stderr)
        return 1

    docs = load_corpus(args.corpus)
    if not docs:
        print(f"ERRO: corpus vazio em {args.corpus}", file=sys.stderr)
        return 1

    per_tribunal = aggregate(docs)

    args.out.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    out_path = args.out / f"per_tribunal_{today}.json"
    payload = {
        "corpus_size": len(docs),
        "per_tribunal": per_tribunal,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print_table(per_tribunal)
    print(f"\nMetrics written to: {out_path}")

    # Gate: routable tribunals com docs precisam >= 80% prazo extraction
    fail = False
    for trib, m in per_tribunal.items():
        if trib not in ROUTABLE:
            continue
        if m["n_with_expected_prazo"] == 0:
            continue
        if m["prazo_extraction_rate"] < PRAZO_THRESHOLD:
            print(
                f"[ALERTA] {trib} prazo_extraction_rate "
                f"{m['prazo_extraction_rate']:.2%} < {PRAZO_THRESHOLD:.0%}",
                file=sys.stderr,
            )
            fail = True
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
