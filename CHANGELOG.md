# Changelog

All notable changes to LegalOps BR.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-28

First production-ready release. LGPD-first pipeline para intimacoes TJ
multi-tribunal com gates network + application + audit + egress.

### Added
- M365 ingest real (OAuth client_credentials + Graph API fetch, stdlib urllib)
- Parsers standalone para TJSC (e-Proc) e TJRJ (PJe) com regex tribunal-specific
- `tribunal_detector` multiplex via sender domain + header fingerprint
- CLI `--config` flag (TOML loader, defaults aplicaveis aos subcomandos)
- CLI `--sender` flag em `pipeline` + `notify` (forca deteccao tribunal)
- CLI `--version` flag
- Edge cases tests (17): empty/malformed CNJ/UTF8/large input/FP defense
- Validate pipeline E2E expandido (8 casos multi-tribunal)
- Benchmark script (`benchmark_pipeline.py`) — 12.9k docs/sec baseline
- Per-type metrics no `measure_redactor.py` (recall + precision por tipo)
- Dockerfile multi-stage + `.dockerignore` + `legalops.toml.example`
- `RUNBOOK.md` operacional (checklist + incident response + LGPD compliance)
- `ARCHITECTURE.md` com pipeline diagram + gates LGPD
- `SECURITY.md` policy
- LICENSE Apache-2.0
- `py.typed` marker (PEP 561 — distribuicao com type hints)

### Changed
- TJSP parser: ParseResult re-exporta do TJPR (type unity no orchestrator)
- TJPR sentenca regex fix: `\bsenten[çc]a\b` (mesmo bug do TJSP corrigido)
- Pre-commit no-real-pii hook: `printf` quebra literais pra evitar self-match
- orchestrator usa `_PARSERS` dict pra rotear; audit log inclui campo `tribunal`
- README v1.0 status + ARCHITECTURE link

### Fixed
- PIIRedactor encoding: UTF-8 com acentos pt-BR preservados
- Edge case: invalid CPF/CNPJ numerico nao redigido (validator gate)
- Pre-commit hook self-match em `.pre-commit-config.yaml`

### Security
- Stdlib only (zero dep network external — urllib pra M365, sem httpx)
- M365 token cache com -30s margem expiry
- M365: erros nao logam body (apenas message_id + sender)
- Audit log: regex pre-insert rejeita PII em metadata

### Metrics (corpus 500 sintetico)
- Recall por tipo: CPF 1.0, CNPJ 1.0, OAB 1.0, EMAIL 1.0, PIX_UUID 1.0, PHONE_BR 1.0
- Precision por tipo: 1.0 em todos 6 tipos
- Leak rate: 0/500 docs
- Throughput: 12954 docs/sec full pipeline
- Tests: 362/362 passing
- Type-check: mypy --strict clean (19 src modulos)
- Lint: ruff clean

## [0.3.0] — 2026-05-28

### Added
- Parsers TJSP (e-SAJ/PJe-SP) com regex tribunal-specific
- Subagents `~/.claude/agents/` (generator/orchestrator/planner — uso local)
- Corpus 500 sintetico (5 templates Projudi + e-SAJ)
- Validate pipeline E2E (5 casos TJPR)

### Changed
- `tribunal_detector` adiciona TJSP rota
- orchestrator multiplex parser por tribunal

## [0.2.0] — 2026-05-22

### Added
- `br_validators.py`: CPF/CNPJ modulo 11 (Receita Federal)
- PIIRedactor: `CPF_NUMERIC`/`CNPJ_NUMERIC` patterns com `PATTERN_VALIDATORS` gate
- Config TOML loader (`config.py`)
- Pre-commit hooks (ruff/mypy/pytest/no-real-pii)
- Recesso forense multi-tribunal (STJ/STF/TRF4/TST/TJPR)

## [0.1.0] — 2026-05-21

Initial PoC release.

### Added
- `pii_redactor`: 7 patterns BR (CPF/CNPJ/RG/OAB/PIX/email/phone) com SHA-256 salted placeholders
- `cpc_prazos`: calc CPC/2015 deterministico
- `tjpr_parser`: parse emails Projudi via regex
- `oab_sigilo`: audit log SHA-256 chain SQLite
- `lgpd_specifics`: constantes LGPD
- `bacen_cvm_feeds`: parser RSS BACEN/CVM
- `practice_profile`: profile escritorio (sem PII)
- `whatsapp_notifier`: bridge.js client stdlib
- `eml_reader`: parser RFC 822 stdlib
- `orchestrator`: pipeline encadeado
- `cli`: argparse subcommands
- Corpus 200 sintetico
- GalileuCLI integration (proxy MITM defense-in-depth)
