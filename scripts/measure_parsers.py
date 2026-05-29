"""Mede metricas POR PARSER diretamente (sem orchestrator).

Uso:
    uv run python scripts/measure_parsers.py [--corpus DIR] [--out DIR]

Para cada doc, roda o parser correspondente ao seu campo `tribunal`
diretamente sobre o texto. Reporta:
- parse_success_rate: ratio de docs com >= 1 intimacao parseada
- vara_extracted_rate, comarca_extracted_rate, prazo_extracted_rate
- tipo_ato_distribution

Saida: metrics/parsers_YYYYMMDD.json + tabela stdout.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legalops.tjpr_parser import ParseResult  # noqa: E402
from legalops.tjpr_parser import parse_email as parse_tjpr  # noqa: E402
from legalops.tjrj_parser import parse_email as parse_tjrj  # noqa: E402
from legalops.tjsc_parser import parse_email as parse_tjsc  # noqa: E402
from legalops.tjsp_parser import parse_email as parse_tjsp  # noqa: E402

DEFAULT_CORPUS = Path(__file__).parent.parent / "corpus" / "synthetic" / "docs"
DEFAULT_OUT = Path(__file__).parent.parent / "metrics"

PARSERS: dict[str, Callable[[str], ParseResult]] = {
    "tjpr": parse_tjpr,
    "tjsp": parse_tjsp,
    "tjsc": parse_tjsc,
    "tjrj": parse_tjrj,
}


def measure(docs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_parser: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n_docs": 0,
            "n_parsed": 0,
            "n_vara": 0,
            "n_comarca": 0,
            "n_prazo": 0,
            "tipo_counter": Counter(),
        }
    )

    for doc in docs:
        tribunal = str(doc.get("tribunal", "neutro"))
        if tribunal not in PARSERS:
            continue
        parse = PARSERS[tribunal]
        bucket = by_parser[tribunal]
        bucket["n_docs"] += 1

        result = parse(str(doc["text"]))
        if result.total >= 1:
            bucket["n_parsed"] += 1
        for intim in result.intimacoes:
            if intim.vara:
                bucket["n_vara"] += 1
            if intim.comarca:
                bucket["n_comarca"] += 1
            if intim.prazo_dias is not None:
                bucket["n_prazo"] += 1
            bucket["tipo_counter"][intim.tipo_ato] += 1

    out: dict[str, dict[str, Any]] = {}
    for trib, b in by_parser.items():
        n = b["n_docs"]
        n_intim = sum(b["tipo_counter"].values())
        out[trib] = {
            "n_docs": n,
            "parse_success_rate": round(b["n_parsed"] / n, 4) if n else 0.0,
            "n_intimacoes": n_intim,
            "vara_extracted_rate": round(b["n_vara"] / n_intim, 4) if n_intim else 0.0,
            "comarca_extracted_rate": round(b["n_comarca"] / n_intim, 4) if n_intim else 0.0,
            "prazo_extracted_rate": round(b["n_prazo"] / n_intim, 4) if n_intim else 0.0,
            "tipo_ato_distribution": dict(b["tipo_counter"]),
        }
    return out


def print_table(per_parser: dict[str, dict[str, Any]]) -> None:
    print("\n=== Per-Parser Metrics ===")
    header = f"{'parser':<8} {'docs':>5} {'parse':>7} {'vara':>7} {'comarca':>8} {'prazo':>7}"
    print(header)
    print("-" * len(header))
    for trib in sorted(per_parser):
        m = per_parser[trib]
        print(
            f"{trib:<8} {m['n_docs']:>5} {m['parse_success_rate']:>7.2%} "
            f"{m['vara_extracted_rate']:>7.2%} {m['comarca_extracted_rate']:>8.2%} "
            f"{m['prazo_extracted_rate']:>7.2%}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.corpus.exists():
        print(f"ERRO: corpus nao existe em {args.corpus}", file=sys.stderr)
        return 1

    docs = [json.loads(p.read_text()) for p in sorted(args.corpus.glob("doc_*.json"))]
    if not docs:
        print(f"ERRO: corpus vazio em {args.corpus}", file=sys.stderr)
        return 1

    per_parser = measure(docs)

    args.out.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    out_path = args.out / f"parsers_{today}.json"
    payload = {
        "corpus_size": len(docs),
        "per_parser": per_parser,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print_table(per_parser)
    print(f"\nMetrics written to: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
