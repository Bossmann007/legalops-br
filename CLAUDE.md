# LegalOps BR — Project Config

## Modelo
**LegalOS Harness — "O Sócio Invisível"**
Sistema operacional para escritórios de advocacia 1–5 advogados.
Não é SaaS. É capacidade operacional instalada: setup R$2k–4k + manutenção R$400–600/mês.
Design spec completo: `~/docs/superpowers/specs/2026-06-27-legalos-harness-design.md`

## Stack
- Python 3.11+ · Pydantic v2 · pytest · ruff · mypy --strict
- CLI via `legalops.cli:main`
- Dashboard: Node.js 20+ · `dashboard/` (zero runtime deps)
- Build: hatchling · uv

## Commands
```bash
export LEGALOPS_PII_SALT="$(openssl rand -hex 24)"  # obrigatorio — scripts/CLI falham sem
uv run pytest              # 844 expected
uv run pytest --cov        # with coverage (>=95% gate)
uv run ruff check .        # lint
uv run mypy src/           # type check
# Dashboard
cd dashboard && npm start  # :4318
```

## Architecture

### Engine (Python — não modificar sem atualizar testes)
```
src/legalops/
├── cpc_prazos.py         — CPC Art.219/224/229 (dias úteis, feriados, dobro)
├── pii_redactor.py       — LGPD PII redaction
├── tjpr_parser.py        — TJPR scraper/parser
├── tjsp_parser.py        — TJSP scraper/parser
├── tjmg_parser.py        — TJMG scraper/parser
├── tjsc_parser.py        — TJSC scraper/parser
├── tjrj_parser.py        — TJRJ scraper/parser
├── tjdft_parser.py       — TJDFT scraper/parser
├── tribunal_detector.py  — auto-detect tribunal from CNJ number
├── contract_analyzer.py  — red flags + cláusulas + sugestões
├── doc_templates.py      — templates de documentos
├── oab_sigilo.py         — OAB sigilo guardrails + HMAC audit
├── orchestrator.py       — workflow orchestration
├── renewal_watcher.py    — contratos vencendo
├── practice_profile.py   — perfil do escritório
├── lgpd_specifics.py     — LGPD compliance
├── dsar.py               — Data Subject Access Request
├── pia.py                — Privacy Impact Assessment
├── anpd_playbook.py      — ANPD incident response
├── due_diligence.py      — M&A due diligence
├── societario.py         — documentos societários
└── cli.py                — entry point
tests/                     — 844 testes, AAA pattern
```

### Harness (camada cliente — projeto Claude Code nativo, tudo em `.claude/`)
```
.claude/
├── settings.json          — hooks (SessionStart/anti-injection/Stop/PreToolUse)
├── commands/              — /nome (prazo, intimacao, varrer, painel, …)
├── agents/                — subagents (contrato-analista, peticao-drafter, …)
├── skills/                — skills nativos (quarentena-doc)
├── anti-injection/        — hooks de segurança (flag-llm-paste, scan-injection)
├── hooks/                 — scripts auxiliares (briefing, prazo-alerta)
├── memory/                — templates de contexto (memory.local/ = dado real, gitignored)
├── workflows/             — intimacoes-batch
└── memory-manifest.json   — fonte de verdade dos stores locais
```
Instalação = abrir a pasta no Claude Code (projeto nativo, sem `plugin install`).

## Harness Skills
- `/briefing` — prazos urgentes + agenda do dia
- `/prazo` — calcular prazo CPC com feriados
- `/processo` — status de processo em TJ
- `/contrato` — análise de contrato + red flags
- `/peticao` — rascunho de petição (sempre DRAFT)
- `/honorarios` — fechar mês / relatório financeiro
- `/dsar` — processar solicitação LGPD
- `/revisao-semanal` — reunião semanal: operações + mercado + IA

## Rules
- Type hints obrigatórios em funções públicas
- Cobertura mínima: 95% (código crítico jurídico)
- NUNCA dados reais de processo em tests — usar faker
- Prazos: validar contra CPC Art. 219 (dias úteis)
- Qualquer output de documento: prefixar com `DRAFT — Requer revisão e assinatura`
- OAB sigilo: conteúdo jurídico sensível → `oab_sigilo` antes de logar

## LGPD
- PII em documentos jurídicos = dado sensível
- Redaction antes de qualquer log via `pii_redactor`
- Anonimizar para dev/test — `faker` + CPF sintético
- Clientes: aliases only (`CLI-021`, hash) — nunca nome real em banco/log

## Status
v1.6.0 · 844 testes (95% cov) · GitHub privado: Bossmann007/legalops-br
Harness = projeto Claude Code nativo (tudo em `.claude/`; hooks em `.claude/settings.json`). Sem plugin install — ela abre a pasta.
Notificação: PULL (/painel Artifact + /briefing); push e dashboard Node deprecated.
Fase A ✅ (prazos + oracle anti-alucinação: /intimacao, dual-extract, validar-extracao, calc-disponivel).
Fase B ✅ (contratos/operação → subagents: contrato-analista, operacao-ledger).
Subagents de fork (isolam contexto): peticao-drafter (opus, /peticao), varredura-triagem (sonnet, triage do /varrer).
Fase B1 ✅ (ingestão email: /varrer, triagem, scan-state "não-olhei ≠ nada-novo", guia de comandos).
Próximo (fechamento técnico): verificar conector MCP M365 no plano dela · smoke de abrir a pasta no Claude Code dela (discovery de commands/agents/hooks nativos) · shadow-run humano ~2 sem (critério de pronto real). Adiado: B2 re-auth guiado.
