# LegalOps BR — Project Config

## Stack
- Python 3.11+ · Pydantic v2 · pytest · ruff · mypy --strict
- CLI via `legalops.cli:main`
- Build: hatchling · uv

## Commands
```bash
uv run pytest              # run all tests (296 expected)
uv run pytest --cov        # with coverage
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
v0.2 · 296/296 testes · GitHub público: Bossmann007/legalops-br
Próximo: piloto Tia May (7 Claude Projects)
