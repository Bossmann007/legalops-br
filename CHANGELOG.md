# Changelog

All notable changes to LegalOps BR.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [1.3.0] — 2026-05-28

Multi-channel notifications: SMTP email + Slack webhook + fan-out multiplex.

### Added
- `email_notifier.py` — `EmailNotifier` via stdlib `smtplib`/`email.message`. STARTTLS opcional, plain text only (sem HTML, reduz superficie). LGPD: body so com `numero_processo` + `dies_ad_quem` + `prazo_efetivo_dias`. Raises `EmailNotifierError` em falhas SMTP.
- `slack_notifier.py` — `SlackNotifier` via stdlib `urllib`. POST `{text, channel?}` para incoming webhook. LGPD: text so com processo + dies_ad_quem. Raises `SlackNotifierError` em falhas HTTP.
- `notification_multiplex.py` — `NotificationMultiplex.notify_all()` faz fan-out para N canais registrados via `add_channel(name, callable)`. Threshold `min_prazo_dias` filtra urgentes; quiet hours suprime tudo na janela (suporta janelas que cruzam meia-noite). Erro por canal eh isolado: loga + zero, segue outros canais.
- `legalops notify` ganha `--channels whatsapp,email,slack`, `--min-prazo-days`, `--quiet-start`, `--quiet-end`. Backwards-compat: sem `--channels` mantem comportamento single-WhatsApp anterior.
- `config.py` ganha secoes `[email]`, `[slack]`, `[notification]` no TOML; `LegalOpsConfig` extendido com defaults.

### Tests
- 30+ testes novos: `test_email_notifier.py` (12) · `test_slack_notifier.py` (10) · `test_notification_multiplex.py` (8). Total: 426 → 456+.

## [1.2.0] — 2026-05-28

Observability v1: structured logs + Prometheus metrics + health CLI.

### Added
- `obs.py` — `JsonFormatter` + `get_logger()` com configure-once idempotente. Honra `LEGALOPS_LOG_LEVEL` / `LEGALOPS_LOG_JSON`. LGPD: filtra CPF/CNPJ/OAB/EMAIL/PIX_UUID das mensagens e extras antes de emitir.
- `metrics.py` — `MetricsRegistry` thread-safe (counter/gauge/histogram) com render Prometheus text exposition. Buckets default `[0.001, 0.01, 0.1, 1.0, 10.0]`s. Stdlib only.
- `legalops health` CLI — checks de pii_redactor / cpc_prazos / tribunal_detector / audit_chain (opcional `--audit-db`). Flags `--format json|text`, `--metrics`. Exit 0/1 conforme status.
- `legalops metrics` CLI — pipeline sintetico + Prometheus exposition em stdout (smoke utility).
- 24+ testes novos: `test_obs.py` (9) · `test_metrics.py` (11) · `test_cli_health.py` (6).

## [1.1.0] — 2026-05-28

Multi-tribunal expand: 6 tribunais cobertos.

### Added
- `tjdft_parser.py` — TJDFT e-SAJ (Distrito Federal, CNJ 8.07)
- `tjmg_parser.py` — TJMG PJe (Minas Gerais, CNJ 8.13)
- `tribunal_detector` ampliado pra `tjdft`/`tjmg` + detection priority (TJDFT antes TJSP devido e-SAJ ambiguity)
- 26 novos tests (13 TJDFT + 13 TJMG) + TestTJDFT/TestTJMG no detector (6 tests)
- 4 templates novos (2 TJDFT + 2 TJMG) no corpus generator
- Corpus generator `--tribunal {all|neutro|tjpr|tjsp|tjsc|tjrj|tjdft|tjmg}` flag
- `scripts/measure_per_tribunal.py` — routing accuracy + prazo extraction per-tribunal
- `scripts/measure_parsers.py` — direct per-parser metrics (parse/vara/comarca/prazo/tipo)
- 5 tests novos pra measure scripts

### Changed
- Detection order: TJDFT header avaliado antes TJSP (e-SAJ shared)
- orchestrator `_PARSERS` dict: +tjdft +tjmg

### Metrics (corpus 500)
- Routing accuracy: 100% all 6 tribunals
- Tests: 399/399 passing

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
