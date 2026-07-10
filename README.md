# LegalOps BR

Sócio Invisível para escritórios de advocacia 1–5 advogados: prazos CPC, intimações,
análise de contratos, LGPD e painel operacional — tudo por comandos `/`, local-first,
**nenhuma chamada automática a LLM externa**. Extensões brasileiras sobre o
**Claude for Legal** (Anthropic, Apache 2.0).

---

## Por onde começar

- 👩‍⚖️ **É a advogada / vai usar?** → **[GUIA-TIA.md](GUIA-TIA.md)** (instalação + uso, sem tecnês).
- 🛠️ **É dev / vai manter?** → arquitetura, runbook e segurança em **[.claude/docs/](.claude/docs/)**.

O harness (comandos, agents, memória, regras, hooks) vive em **`.claude/`** — é um projeto
Claude Code nativo. O motor determinístico é o pacote Python `legalops` em `src/`.

---

## Status

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-844-brightgreen.svg)](tests/)
[![mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](pyproject.toml)

v1.6.0 · 844 testes (95% cov) · `mypy --strict` + `ruff` clean · 0 PII leaks (corpus sintético).

**Cobre:** redação PII (7 patterns BR) · cálculo CPC determinístico (feriados/recesso/dobro) ·
6 tribunais (TJPR/SP/SC/RJ/DFT/MG) · ingestão de e-mail M365 · análise de contrato (CDC) ·
M&A/Due Diligence · LGPD (DSAR/RIPD/DPA/ANPD) · audit chain SHA-256.

Detalhe de módulos e pipeline: [.claude/docs/ARCHITECTURE.md](.claude/docs/ARCHITECTURE.md).

---

## Setup (dev)

```bash
uv venv --python 3.11 && uv pip install -e ".[dev]"
export LEGALOPS_PII_SALT="$(openssl rand -hex 24)"   # obrigatório; guarde em secret manager
uv run pytest                                        # 844 esperados
uv run python tests/corpus/synthetic/generate.py --count 200   # corpus p/ test_egress
```

Instalação da advogada (Windows): use **[GUIA-TIA.md](GUIA-TIA.md)** / `setup.ps1`.
Manutenção e operação: [.claude/docs/RUNBOOK.md](.claude/docs/RUNBOOK.md).

## CLI (motor)

```bash
echo "CPF 123.456.789-00 teste" | legalops redact     # redige PII
legalops pipeline --input email.txt --audit-db audit.db --hoje AAAA-MM-DD
legalops audit verify --db audit.db
```

## Segurança / LGPD

Local-first, **nenhum dado real** em código/testes/commits. Redação PII antes de qualquer log.
Cliente por alias. Camadas de egresso e postura de segurança:
[.claude/docs/SECURITY.md](.claude/docs/SECURITY.md).

## Licença

Apache-2.0 — herda do Claude for Legal upstream. Ver [.claude/docs/CHANGELOG.md](.claude/docs/CHANGELOG.md).
