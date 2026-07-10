"""Benchmark pipeline: throughput por modulo no corpus 500.

Mede tempo de cada estagio (redact, parse, calc_prazo) em ms/doc e total.

Uso:
    uv run python scripts/benchmark_pipeline.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legalops.orchestrator import process_email  # noqa: E402
from legalops.pii_redactor import PIIRedactor  # noqa: E402
from legalops.tjpr_parser import parse_email as parse_tjpr  # noqa: E402

CORPUS_DIR = Path(__file__).parent.parent / "corpus" / "synthetic" / "docs"
OUT_DIR = Path(__file__).parent.parent / "metrics"


def main() -> int:
    if not CORPUS_DIR.exists():
        print("ERRO: corpus nao existe.", file=sys.stderr)
        return 1

    docs = [json.loads(p.read_text()) for p in sorted(CORPUS_DIR.glob("doc_*.json"))]
    n = len(docs)
    if n == 0:
        print("ERRO: corpus vazio.", file=sys.stderr)
        return 1

    redactor = PIIRedactor()

    # Stage 1: redact only
    t0 = time.perf_counter()
    for doc in docs:
        redactor.redact(doc["text"])
        _ = doc["text"]
    redact_ms = (time.perf_counter() - t0) * 1000

    # Stage 2: parse only (TJPR engine)
    redacted_texts = [redactor.redact(doc["text"]).redacted_text for doc in docs]
    t0 = time.perf_counter()
    for txt in redacted_texts:
        parse_tjpr(txt)
    parse_ms = (time.perf_counter() - t0) * 1000

    # Stage 3: orchestrator (full pipeline)
    t0 = time.perf_counter()
    n_intimacoes = 0
    for doc in docs:
        results = process_email(doc["text"], parte="particular")
        n_intimacoes += len(results)
    pipeline_ms = (time.perf_counter() - t0) * 1000

    metrics = {
        "corpus_size": n,
        "redact_ms_total": round(redact_ms, 2),
        "redact_ms_per_doc": round(redact_ms / n, 3),
        "parse_ms_total": round(parse_ms, 2),
        "parse_ms_per_doc": round(parse_ms / n, 3),
        "pipeline_ms_total": round(pipeline_ms, 2),
        "pipeline_ms_per_doc": round(pipeline_ms / n, 3),
        "total_intimacoes": n_intimacoes,
        "docs_per_sec": round(n / (pipeline_ms / 1000), 1),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    out_path = OUT_DIR / f"benchmark_{today}.json"
    out_path.write_text(json.dumps(metrics, indent=2))

    print("\n=== Pipeline Benchmark ===")
    print(f"Corpus:               {n} docs")
    print(f"Redact only:          {metrics['redact_ms_per_doc']} ms/doc")
    print(f"Parse only:           {metrics['parse_ms_per_doc']} ms/doc")
    print(f"Full pipeline:        {metrics['pipeline_ms_per_doc']} ms/doc")
    print(f"Throughput:           {metrics['docs_per_sec']} docs/sec")
    print(f"Total intimacoes:     {n_intimacoes}")
    print(f"\nMetrics written to:  {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
