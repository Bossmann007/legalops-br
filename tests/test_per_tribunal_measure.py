"""Smoke tests para scripts/measure_per_tribunal.py e scripts/measure_parsers.py.

AAA pattern: Arrange (build small corpus) / Act (invoke main) / Assert.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"


def _write_doc(out_dir: Path, idx: int, doc: dict[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"doc_{idx:04d}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8"
    )


def _run(script: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def mini_corpus(tmp_path: Path) -> Path:
    # Arrange: corpus minimo com 1 doc por tribunal routable + 1 neutro
    docs_dir = tmp_path / "docs"
    _write_doc(
        docs_dir,
        0,
        {
            "id": "t-0",
            "text": (
                "Sistema Projudi - Tribunal de Justica do Parana\n"
                "Processo: 1234567-89.2025.8.16.0001\n"
                "Vara: 2a Vara Civel - Comarca de Curitiba\n"
                "Despacho: Intime-se no prazo de 15 dias. Publicado em 10/03/2025."
            ),
            "expected_pii_count": 0,
            "expected_by_type": {},
            "tribunal": "tjpr",
        },
    )
    _write_doc(
        docs_dir,
        1,
        {
            "id": "t-1",
            "text": (
                "Tribunal de Justica de Sao Paulo - e-SAJ\n"
                "Autos nro 7654321-12.2025.8.26.0100\n"
                "3a Vara Civel - Foro Regional de Santo Amaro\n"
                "Decisao: prazo de 10 dias. Publicado em 12/04/2025."
            ),
            "expected_pii_count": 0,
            "expected_by_type": {},
            "tribunal": "tjsp",
        },
    )
    _write_doc(
        docs_dir,
        2,
        {
            "id": "t-2",
            "text": "Documento sem dados pessoais.",
            "expected_pii_count": 0,
            "expected_by_type": {},
            "tribunal": "neutro",
        },
    )
    return docs_dir


def test_per_tribunal_creates_output(mini_corpus: Path, tmp_path: Path) -> None:
    # Arrange
    out_dir = tmp_path / "metrics"
    # Act
    proc = _run(
        "measure_per_tribunal.py",
        ["--corpus", str(mini_corpus), "--out", str(out_dir)],
    )
    # Assert
    assert proc.returncode in (0, 1), proc.stderr
    files = list(out_dir.glob("per_tribunal_*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text())
    assert payload["corpus_size"] == 3
    assert "per_tribunal" in payload
    assert "tjpr" in payload["per_tribunal"]


def test_per_tribunal_structure_complete(mini_corpus: Path, tmp_path: Path) -> None:
    # Arrange
    out_dir = tmp_path / "metrics"
    # Act
    _run("measure_per_tribunal.py", ["--corpus", str(mini_corpus), "--out", str(out_dir)])
    payload = json.loads(next(out_dir.glob("per_tribunal_*.json")).read_text())
    # Assert: cada tribunal tem chaves esperadas
    required = {
        "n_docs",
        "n_intimacoes_detected",
        "parsers_routing_accuracy",
        "prazo_extraction_rate",
    }
    for trib_metrics in payload["per_tribunal"].values():
        assert required.issubset(trib_metrics.keys())


def test_per_tribunal_missing_corpus_exits_1(tmp_path: Path) -> None:
    # Arrange / Act
    proc = _run(
        "measure_per_tribunal.py",
        ["--corpus", str(tmp_path / "nao_existe"), "--out", str(tmp_path)],
    )
    # Assert
    assert proc.returncode == 1


def test_measure_parsers_creates_output(mini_corpus: Path, tmp_path: Path) -> None:
    # Arrange
    out_dir = tmp_path / "metrics"
    # Act
    proc = _run(
        "measure_parsers.py",
        ["--corpus", str(mini_corpus), "--out", str(out_dir)],
    )
    # Assert
    assert proc.returncode == 0, proc.stderr
    files = list(out_dir.glob("parsers_*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text())
    assert payload["corpus_size"] == 3
    # Apenas parsers routable aparecem (tjpr + tjsp, neutro nao tem parser)
    assert "tjpr" in payload["per_parser"]
    assert "tjsp" in payload["per_parser"]
    assert "neutro" not in payload["per_parser"]


def test_measure_parsers_metric_keys(mini_corpus: Path, tmp_path: Path) -> None:
    # Arrange
    out_dir = tmp_path / "metrics"
    # Act
    _run("measure_parsers.py", ["--corpus", str(mini_corpus), "--out", str(out_dir)])
    payload = json.loads(next(out_dir.glob("parsers_*.json")).read_text())
    # Assert
    required = {
        "n_docs",
        "parse_success_rate",
        "vara_extracted_rate",
        "comarca_extracted_rate",
        "prazo_extracted_rate",
        "tipo_ato_distribution",
    }
    for parser_metrics in payload["per_parser"].values():
        assert required.issubset(parser_metrics.keys())
