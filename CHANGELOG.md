# Changelog

All notable changes to LegalOps BR.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **pii_redactor**: removido salt público fixo (`legalops-br-v0.1`). Salt secreto agora
  obrigatório via `LEGALOPS_PII_SALT` (>=16 bytes); hash do audit migrado de SHA-256 salted
  para **HMAC-SHA256**. Sem salt secreto o hash de CPF/CNPJ era reversível por força bruta
  (espaço pequeno + salt público) — pseudonimização não-conforme (Art. 13 LGPD). `MissingSaltError`
  se ausente. CLI sai com código 2 e mensagem acionável.
- **Confidencialidade**: removida identificação real do cliente (nome do escritório e da
  advogada) de todos os arquivos rastreados; módulo de profile do escritório renomeado para
  `practice_profile` com placeholders genéricos. Hook `no-real-pii-fulltree` (pre-push) agora
  varre o repo inteiro, não só o diff staged.

- **oab_sigilo (audit log)**: tamper-evidence opcional via HMAC-SHA256. Aceita `hmac_key=`
  ou env `LEGALOPS_AUDIT_HMAC_KEY`. Sem chave, mantém SHA-256 puro (detecta corrupção
  acidental, não rewrite deliberado). Com chave, um atacante que rewrita a tabela inteira
  não consegue recomputar hashes válidos. `verify_chain()` agora usa `hmac.compare_digest`
  (comparação em tempo constante).
- **config (SMTP password)**: senha SMTP em texto plano no TOML deixa de ser único caminho.
  Env `LEGALOPS_SMTP_PASSWORD` tem precedência. Aviso (`UserWarning`) quando o `config.toml`
  contém `email.password` E tem permissões frouxas (grupo/outros podem ler) — recomenda
  `chmod 600` ou env var.
- **pii_redactor (PHONE_BR)**: regex agora exige hífen no número local (`\d{4}-\d{4}`).
  Antes, um número bare de 11 dígitos (CPF sem máscara) podia ser engolido como `PHONE_BR`
  por casar parcialmente, mascarando o gate de validação de CPF.
- **pii_redactor (overlap)**: dedup de matches usa overlap de intervalos em vez de igualdade
  estrita de spans — evita match duplicado quando um padrão menor está contido em outro.
- **m365_ingest (OData injection)**: `sender_filter` agora escapa aspa simples (`'` → `''`)
  antes de compor o `$filter` — defesa em profundidade contra injeção de OData.

### Changed
- `orchestrator.process_email(redactor_salt=...)` aceita `None` (lê de `LEGALOPS_PII_SALT`).

### Added (MVP launch prep — 2026-05-29 session 4)
- **CI** (`.github/workflows/ci.yml`): synthetic `LEGALOPS_PII_SALT` env injetado
  no nivel do workflow (`env:`) — scripts e tests passam a rodar; salt em prod
  via secret manager.
- **`.env.example`**: template completo com `LEGALOPS_PII_SALT` (obrigatorio),
  `LEGALOPS_AUDIT_HMAC_KEY` + `LEGALOPS_SMTP_PASSWORD` (opcionais) + creds M365.
- **Cobertura ≥95%** (era 92%): novos tests `test_cli_helpers.py` (helpers +
  health + notify dry-run + audit verify), `test_eml_reader.py` expandido
  (max_files, attachment, bad date, empty body), parsers TJSC/TJRJ (empty,
  no CNJ, tipo desconhecido, datas invalidas, cartorio fallback). Total: **810
  tests · 95% cov**.
- **Docs**: README badge + RUNBOOK actualizados (763→810/810). RUNBOOK adiciona
  `export LEGALOPS_PII_SALT` no checklist pre-release + entries pra
  `validate_pipeline.py`/`measure_redactor.py`/`benchmark_pipeline.py`.

### Notes
- **L4 XML (defusedxml)**: `bacen_cvm_feeds.parse_feed_xml` recebe `xml_text`
  como argumento — nao faz fetch remoto. Sem caller passando XML hostil, XXE
  e risco hipotetico. Decisao: ficar fora do MVP. Quando passar a aceitar feeds
  remotos (v0.3+), adicionar `defusedxml.ElementTree` (unica dep externa
  justificada por regra "stdlib only" — security trumps).

## [1.5.0] — 2026-05-29

LGPD assistant: DSAR (direitos do titular) + PIA/RIPD + DPA + playbook ANPD + revisão de
fornecedores de IA. Entrega o **tooling determinístico BR** da fase **v1.4 do roadmap de
produto**. Camada de prompts/Claude Projects continua dependente da Tia May (fora do repo).

> Nota de versionamento: SemVer técnico (1.x) ≠ fases de produto (v1.x). A release `1.5.0`
> implementa a fase de produto **v1.4**.

### Added — fase produto v1.4 (LGPD assistant)
- `dsar.py` — `classify_request()` mapeia texto livre → direito do titular (Art. 18); `processar_dsar()` calcula prazo de resposta (15 dias, Art. 19), status (no_prazo/vence_hoje/em_atraso) e texto-padrão pt-BR. `DSARError` para código desconhecido. Roda após pii_redactor.
- `pia.py` — `avaliar_ripd()` produz Relatório de Impacto (Art. 38): riscos curados por categoria de dado/base legal/princípios, score ponderado e nível. Cada risco aparece **uma única vez** (sem duplicação de avisos); nível acompanha o pior risco isolado ou o score acumulado.
- `dpa_templates.py` — `render_dpa()` + `clausulas_obrigatorias()` (8 cláusulas: objeto/escopo/segurança/subcontratação/incidente/titular/eliminação/auditoria). Campos ausentes viram placeholder, nunca lança.
- `anpd_playbook.py` — `avaliar_severidade()` + `gerar_plano()` para incidente de segurança: prazo de comunicação à ANPD em **dias úteis** (Art. 48) + `conteudo_minimo_comunicacao()`.
- `vendor_ai_review.py` — `checklist_vendor_padrao()` (10 itens: Art. 33/39/7/16/46/20/37/48/41) + `VendorReview.set_status/flags/score/aprovado` para avaliar fornecedores de IA sob LGPD.
- `legalops dsar` CLI — processa requisição de titular; redige PII por padrão (`--skip-redact`), classifica direito ou aceita `--direito`, calcula prazo.

### Changed
- `pia.avaliar_ripd()` — removida a conversão genérica dos avisos de `validar_operacao` em riscos, que duplicava a mesma questão (ex.: Art. 14) com severidades conflitantes. Nível agora = `max(classificação por score, pior risco isolado)`.

### Tests
- +90 testes: dsar/pia/dpa (46) · anpd/vendor (41) · CLI dsar (3). Total: 649 → 739.

### Mapeamento versão técnica × fase produto
| Fase roadmap | Entrega | Módulos | Versão técnica |
|--------------|---------|---------|----------------|
| v1.4 | LGPD assistant | dsar, pia, dpa_templates, anpd_playbook, vendor_ai_review | 1.5.0 |

## [1.4.0] — 2026-05-29

Camada de capacidades jurídicas: documentos estruturados + Contract AI + M&A/Due Diligence.
Entrega o **tooling determinístico BR** das fases **v1.1, v1.2 e v1.3 do roadmap de produto**
(`LegalOps — Roadmap.md`). A camada de prompts/Claude Projects (interface claude.ai) depende
da Tia May e fica fora do repo.

> Nota de versionamento: o SemVer do repositório (1.x) ≠ as fases do roadmap de produto (v1.x).
> Esta release técnica `1.4.0` implementa as fases de produto **1.1 → 1.3**. Mapeamento abaixo.

### Added — fase produto v1.1 (Procurações e contratos estruturados)
- `doc_extractor.py` — `extract_procuracao()` / `extract_contrato_honorarios()` via regex. Dataclasses `ProcuracaoCampos` / `ContratoHonorariosCampos` com `campos_ausentes` + `confianca`. Roda após pii_redactor; não loga conteúdo.
- `doc_templates.py` — `render_procuracao()` / `render_contrato_honorarios()`; campos ausentes viram `[A PREENCHER: <campo>]`, nunca lança.
- `approval_gate.py` — `ApprovalGate` sobre `AuditLog`: `request/approve/reject/commit/pending`. "Nenhuma escrita em ficha/financeiro sem aprovação explícita." `commit()` antes de aprovação levanta `ApprovalError`. Audit recebe só change_id/resource/status (payload nunca vai ao log).

### Added — fase produto v1.2 (Contract AI)
- `contract_analyzer.py` — `scan_clausulas_abusivas()` (CDC Art. 51 + Súmulas STJ 539/541), `analisar_financiamento()` (spread/indexador/capitalização/IOF), `scan_nda()`, `analisar_contrato()` → `RelatorioRisco` pontuado (score + nível baixo/médio/alto + recomendações).
- `renewal_watcher.py` — `RenewalWatcher` monitora vencimento + aviso prévio; `check(hoje)` → alertas ordenados por urgência (vencido/crítico/atenção/ok). LGPD: só id + descrição + datas.
- `legalops contract` CLI — analisa risco de contrato; redige PII por padrão (`--skip-redact` opcional).

### Added — fase produto v1.3 (M&A + Due Diligence) ⭐ prioridade Tia May
- `societario.py` — `detect_tipo_sociedade()`, `quorum_deliberacao()` (CC/2002 arts. 1.061/1.071/1.076 + Lei 6.404), `validar_participacoes()`. Dataclasses `Socio` / `EstruturaSocietaria`.
- `due_diligence.py` — `checklist_padrao()` (5 áreas: trabalhista/fiscal/ambiental/contratual/societário), `gaps()`, `score()`, `resumo_por_area()`. Referências CVM/Junta/Receita.
- `data_room.py` — `classify_document()` + `DataRoomIndex.auditar_completude()` (detecta categorias requeridas ausentes).
- `disclosure.py` — `find_gaps()` / `inconsistencias()` para disclosure schedules.
- `red_flags.py` — `scan_acquisition_contract()` detecta change of control / MAC / cap de indenização / survival R&W / non-compete / earn-out, **incluindo ausências de risco** (`mac_ausente`, `sem_cap_indenizacao`).

### Tests
- +183 testes: docs (72) · M&A/DD (75) · Contract AI (36). Total: 464 → 649+.

### Mapeamento versão técnica × fase produto
| Fase roadmap | Entrega | Módulos | Versão técnica |
|--------------|---------|---------|----------------|
| v1.1 | Docs estruturados | doc_extractor, doc_templates, approval_gate | 1.4.0 |
| v1.2 | Contract AI | contract_analyzer, renewal_watcher | 1.4.0 |
| v1.3 | M&A + Due Diligence | societario, due_diligence, data_room, disclosure, red_flags | 1.4.0 |

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
