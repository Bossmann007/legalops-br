"""Mede precision/recall do pii-redactor-br no corpus sintetico.

Uso:
    uv run python scripts/measure_redactor.py

Saida: metrics/metrics_YYYYMMDD.json + print no stdout.

Metodologia:
- expected_pii_count vem do template do corpus (ground truth de COUNT, nao tipo)
- detected = len(result.matches)
- Aggregate: recall = sum(min(detected, expected)) / sum(expected)
- Per-type leak: regex de cada tipo sobre redacted_text — qualquer hit = leak
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legalops.pii_redactor import PIIRedactor  # noqa: E402

CORPUS_DIR = Path(__file__).parent.parent / "corpus" / "synthetic" / "docs"
OUT_DIR = Path(__file__).parent.parent / "metrics"

LEAK_PATTERNS = {
    "CPF": re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}"),
    "CNPJ": re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"),
    "OAB": re.compile(r"OAB[/-][A-Z]{2}\s?\d+"),
    "EMAIL": re.compile(r"[\w.+-]+@[\w.-]+\.\w+"),
    "PIX_UUID": re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
    "PHONE_BR": re.compile(r"\+?55?\s?\(?\d{2}\)?\s?9?\d{4}-?\d{4}"),
}


def main() -> int:
    if not CORPUS_DIR.exists():
        print(f"ERRO: corpus nao existe em {CORPUS_DIR}", file=sys.stderr)
        print("Rode: python corpus/synthetic/generate.py --count 200", file=sys.stderr)
        return 1

    redactor = PIIRedactor()
    docs = [json.loads(p.read_text()) for p in sorted(CORPUS_DIR.glob("doc_*.json"))]
    n = len(docs)

    total_expected = 0
    total_detected = 0
    type_counter: Counter[str] = Counter()
    expected_by_type: Counter[str] = Counter()
    detected_by_type_tp: Counter[str] = Counter()  # true positives per type
    leak_counter: Counter[str] = Counter()
    docs_with_leak = 0

    for doc in docs:
        expected = int(doc["expected_pii_count"])
        exp_by_type = doc.get("expected_by_type", {})
        result = redactor.redact(doc["text"])
        detected = len(result.matches)

        total_expected += expected
        total_detected += detected
        per_doc_detected: Counter[str] = Counter()
        for m in result.matches:
            type_counter[m.pii_type] += 1
            per_doc_detected[m.pii_type] += 1

        for ptype, exp_n in exp_by_type.items():
            expected_by_type[ptype] += exp_n
            detected_by_type_tp[ptype] += min(per_doc_detected.get(ptype, 0), exp_n)

        doc_had_leak = False
        for label, pat in LEAK_PATTERNS.items():
            for hit in pat.finditer(result.redacted_text):
                if hit.group().startswith("["):
                    continue
                leak_counter[label] += 1
                doc_had_leak = True
        if doc_had_leak:
            docs_with_leak += 1

    recall_count = min(total_detected, total_expected) / total_expected if total_expected else 0
    leak_rate = docs_with_leak / n if n else 0

    recall_by_type: dict[str, float] = {}
    precision_by_type: dict[str, float] = {}
    for ptype, exp_n in expected_by_type.items():
        tp = detected_by_type_tp.get(ptype, 0)
        det = type_counter.get(ptype, 0)
        recall_by_type[ptype] = round(tp / exp_n, 4) if exp_n else 0.0
        precision_by_type[ptype] = round(tp / det, 4) if det else 0.0

    metrics = {
        "corpus_size": n,
        "total_expected_pii": total_expected,
        "total_detected_pii": total_detected,
        "recall_count_based": round(recall_count, 4),
        "leak_rate": round(leak_rate, 4),
        "docs_with_any_leak": docs_with_leak,
        "leaks_by_type": dict(leak_counter),
        "detected_by_type": dict(type_counter),
        "expected_by_type": dict(expected_by_type),
        "recall_by_type": recall_by_type,
        "precision_by_type": precision_by_type,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
    out_path = OUT_DIR / f"metrics_{today}.json"
    out_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))

    print("\n=== PII Redactor Metrics ===")
    print(f"Corpus size:           {n}")
    print(f"Total expected PII:    {total_expected}")
    print(f"Total detected PII:    {total_detected}")
    print(f"Recall (count-based):  {recall_count:.2%}")
    print(f"Leak rate:             {leak_rate:.2%}")
    print(f"Docs with any leak:    {docs_with_leak}/{n}")
    print(f"Detected by type:      {dict(type_counter)}")
    print(f"Expected by type:      {dict(expected_by_type)}")
    print(f"Recall by type:        {recall_by_type}")
    print(f"Precision by type:     {precision_by_type}")
    print(f"Leaks by type:         {dict(leak_counter) if leak_counter else 'NONE'}")
    print(f"\nMetrics written to:    {out_path}")

    if leak_rate > 0:
        print("\n[FALHA] Vazamento detectado — bloquear merge", file=sys.stderr)
        return 1
    if recall_count < 0.80:
        print(f"\n[ALERTA] Recall {recall_count:.2%} < 80%", file=sys.stderr)
        return 2
    print("\n[OK] Sem vazamentos. Recall acima do threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
