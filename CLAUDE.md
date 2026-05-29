# LegalOps BR — Project Config

## Stack
- Python 3.11+ · Pydantic v2 · pytest · ruff · mypy --strict
- CLI via `legalops.cli:main`
- Build: hatchling · uv

## Commands
```bash
export LEGALOPS_PII_SALT="$(openssl rand -hex 24)"  # obrigatorio — scripts/CLI falham sem
uv run pytest              # 811 expected
uv run pytest --cov        # with coverage (>=95% gate)
uv run ruff check .        # lint
uv run mypy src/           # type check
```

## Architecture
```
src/legalops/
├── prazos/     — CPC deadline calculator
├── pii/        — PII redaction (LGPD)
├── tjpr/       — TJPR parser
└── cli.py      — entry point
tests/          — mirrors src/ structure, AAA pattern
```

## Rules
- Type hints obrigatórios em funções públicas
- Cobertura mínima: 95% (código crítico jurídico)
- NUNCA dados reais de processo em tests — usar faker
- Prazos: validar contra CPC Art. 219 (dias úteis)

## LGPD
- PII em documentos jurídicos = dado sensível
- Redaction antes de qualquer log
- Anonimizar para dev/test — `faker` + CPF sintético

## Status
v1.5.0 · 811/811 testes (95% cov) · GitHub privado: Bossmann007/legalops-br
Audit backlog M1/M2/L1/L2/L3 fechado · L4 (defusedxml em bacen_cvm_feeds) deferido v0.3
Próximo: piloto Tia May (7 Claude Projects)
