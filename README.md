# LegalOps BR

Extensoes brasileiras sobre o **Claude for Legal** (Anthropic, Apache 2.0).

Sistema de processamento de intimacoes TJPR com gates LGPD: redacao PII →
parse → calculo CPC determinstico → audit chain SHA-256 → notificacao
WhatsApp. Local-first, **nenhuma chamada automatica a LLM externa**.

---

## Status v1.5.0 — fases produto v1.1→v1.4 (docs + Contract AI + M&A/DD + LGPD assistant)

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-739%2F739-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/PII_recall-100%25-brightgreen.svg)](metrics/)
[![mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](pyproject.toml)
[![ruff](https://img.shields.io/badge/ruff-clean-brightgreen.svg)](pyproject.toml)

- **739/739 tests** passing, `mypy --strict` clean (41 modulos), `ruff` clean
- 100% recall + 100% precision por tipo PII (corpus 500 sintetico, 0 leaks)
- 6 tribunais: TJPR · TJSP · TJSC · TJRJ · TJDFT · TJMG (regex tribunal-specific)
- M365 ingest real (OAuth client_credentials + Graph API, stdlib only)
- Observability: structured logs + Prometheus metrics + `health`/`metrics` CLI
- Multi-channel notify: WhatsApp + SMTP + Slack (threshold + quiet hours)
- **Contract AI**: clausulas abusivas (CDC Art. 51), financiamento, NDA, renewal watcher
- **M&A + Due Diligence**: societario, DD checklist BR, data room, disclosure, red flags
- **Docs estruturados**: extractor/templates procuracao + contrato honorarios + approval gate
- **LGPD assistant**: DSAR (Art. 18/19), PIA/RIPD (Art. 38), DPA, playbook ANPD, vendor AI review
- CLI: `redact`, `parse`, `pipeline`, `batch`, `notify`, `contract`, `dsar`, `health`, `metrics`, `audit`
- Benchmark: 12.9k docs/sec full pipeline (corpus 500)

> **Versionamento:** SemVer do repo (`1.5.0`) ≠ fases do roadmap de produto (v1.1→v1.4).
> A release `1.5.0` entrega o tooling Python das fases de produto 1.1→1.4. Camada de
> prompts/Claude Projects (interface claude.ai) depende da Tia May — fora do repo.

- See [CHANGELOG.md](CHANGELOG.md) · [ARCHITECTURE.md](docs/ARCHITECTURE.md) · [RUNBOOK.md](RUNBOOK.md) · [SECURITY.md](SECURITY.md)

---

## Modulos core

| Modulo | Funcao |
|--------|--------|
| `pii_redactor` | Redacao 7 patterns BR (CPF/CNPJ/RG/OAB/PIX/email/telefone) com SHA-256 salted placeholders |
| `cpc_prazos` | Calculo CPC/2015 — arts. 219/224/231/183/180/186, feriados nacionais + recesso TJPR (20/12–20/01), dobro Fazenda/MP/Defensoria, DJE exception |
| `tjpr_parser` | Parse emails Projudi (TJPR) via regex |
| `tjsp_parser` | Parse emails e-SAJ / PJe-SP (TJSP), reusa engine TJSP |
| `tjsc_parser` | Parse emails e-Proc (TJSC), reusa engine TJSP |
| `tjrj_parser` | Parse emails PJe-RJ (TJRJ), reusa engine TJSP |
| `tribunal_detector` | Rota por sender domain + header fingerprint |
| `br_validators` | Validacao modulo 11 (CPF/CNPJ) — gate pra patterns numericos |
| `eml_reader` | Parser RFC 822 stdlib (text/plain preferido + HTML strip fallback) |
| `orchestrator` | Encadeia pii → parse → prazos → audit; retorna `ProcessedIntimacao` por intimacao |
| `oab_sigilo` | Audit log SHA-256 chain SQLite, BEGIN IMMEDIATE atomic, rejeita PII em metadata |
| `lgpd_specifics` | Constantes LGPD — `BaseLegal`, `TipoDado`, `DIREITOS_TITULAR`, `validar_operacao` |
| `bacen_cvm_feeds` | Parser RSS BACEN/CVM (stdlib xml.etree, XXE-safe) |
| `maffini_practice_profile` | Profile estruturado escritorio (sem PII, placeholders apenas) |
| `whatsapp_notifier` | Cliente HTTP stdlib pra bridge.js :3000, filtra alerta URGENTE |
| `doc_extractor` | Extrai campos de procuracao + contrato honorarios (fase v1.1) |
| `doc_templates` | Render procuracao + contrato honorarios; placeholders `[A PREENCHER]` (v1.1) |
| `approval_gate` | Gate write/rollback sobre AuditLog — sem escrita sem aprovacao (v1.1) |
| `contract_analyzer` | Clausulas abusivas CDC Art. 51 + financiamento + NDA + relatorio risco (v1.2) |
| `renewal_watcher` | Monitor de vencimento de contratos + aviso previo (v1.2) |
| `societario` | Estrutura societaria BR: tipo, quorum CC/2002 + Lei 6.404, participacoes (v1.3) |
| `due_diligence` | Checklist DD BR (trabalhista/fiscal/ambiental/contratual/societario) + gaps (v1.3) |
| `data_room` | Classifica docs do data room + audita completude (v1.3) |
| `disclosure` | Gaps + inconsistencias em disclosure schedules M&A (v1.3) |
| `red_flags` | Red flags em contrato de aquisicao: CoC/MAC/cap/survival/non-compete/earn-out (v1.3) |
| `dsar` | Requisicao de titular (Art. 18): classifica direito + calcula prazo resposta 15d (Art. 19) (v1.4) |
| `pia` | RIPD/PIA (Art. 38): riscos curados + score + nivel; sem duplicacao de risco (v1.4) |
| `dpa_templates` | Render DPA + 8 clausulas obrigatorias (objeto/seguranca/incidente/auditoria) (v1.4) |
| `anpd_playbook` | Incidente de seguranca: severidade + prazo comunicacao ANPD em dias uteis (Art. 48) (v1.4) |
| `vendor_ai_review` | Checklist 10 itens LGPD pra fornecedor de IA (Art. 33/39/7/16/46/20/37/48/41) (v1.4) |
| `cli` | argparse — `redact`, `parse`, `pipeline`, `batch`, `notify`, `contract`, `dsar`, `health`, `metrics`, `audit` |

---

## Stack

- Python 3.11+
- uv (gestor)
- pytest + ruff + mypy strict
- GalileuCLI (Go, https://github.com/eubrunocase/GalileuCLI) — proxy MITM defesa em profundidade

---

## Setup

```bash
uv venv --python 3.11
uv pip install -e ".[dev]"
uv run pytest
```

Após install, comando `legalops` disponivel via entry point `[project.scripts]`.

### Gerar corpus sintetico (necessario para tests/test_egress.py)

```bash
uv run python corpus/synthetic/generate.py --count 200
```

---

## CLI

```bash
# Redact PII de um texto
echo "CPF 123.456.789-00 teste" | legalops redact

# Parse intimacao TJPR
legalops parse --input email.txt

# Pipeline completo (redact + parse + calc + audit)
legalops pipeline --input email.txt --audit-db audit.db --hoje 2026-05-23

# Batch — processa diretorio de .eml
legalops batch --dir ~/inbox-tjpr/ --audit-db ~/audit.db --hoje 2026-05-23

# Notify — pipeline + envia urgentes via WhatsApp bridge
legalops notify --input email.txt \
  --chat-id "5541999999999@s.whatsapp.net" \
  --dry-run

# Audit
legalops audit verify --db audit.db
legalops audit list --db audit.db
```

---

## Pipeline integrado

```
Outlook .eml → eml_reader → pii_redactor → tjpr_parser → cpc_prazos
                                                              ↓
                                                       oab_sigilo (audit chain)
                                                              ↓
                                                  whatsapp_notifier → bridge :3000
```

Defesa em profundidade:

1. **Aplicacional** — `pii_redactor` bloqueia PII bruto
2. **Network** — `GalileuCLI` proxy MITM intercepta egress
3. **Audit** — `oab_sigilo` SHA-256 chain rejeita PII em metadata
4. **Humano** — Tia May aprova item-a-item antes do envio WhatsApp

---

## Galileu proxy (opcional, defesa em profundidade)

```bash
cd proxy/galileu
/home/bossmann/Projects/galileu-cli/galileu --dry-run

# Instalar CA cert (Arch Linux)
sudo cp galileu-ca.pem /etc/ca-certificates/trust-source/anchors/galileu.crt
sudo trust extract-compat

# Configurar Claude Code / Cursor
HTTPS_PROXY=http://localhost:9000 claude
```

---

## Comandos uteis

```bash
uv run pytest                                  # tests
uv run ruff check src tests scripts corpus     # lint
uv run mypy src                                # type check
uv run python scripts/validate_pipeline.py     # E2E validation
uv run python scripts/measure_redactor.py      # recall + leak rate metrics
```

---

## Roadmap

Ver `LegalOps — Roadmap.md` no vault Mafioso ou `docs/`. **Tooling Python (este repo):**
- v0.1 PoC ✅ · v1.0 production-ready (prazos/parsers/PII/audit/M365) ✅
- fase produto **v1.1** — docs estruturados (procuracao/contrato + approval gate) ✅ tooling
- fase produto **v1.2** — Contract AI (clausulas abusivas + financiamento + renewal) ✅ tooling
- fase produto **v1.3** — M&A + Due Diligence (societario/DD/data room/disclosure/red flags) ✅ tooling
- fase produto **v1.4** — LGPD assistant (DSAR/PIA/DPA/ANPD/vendor AI review) ✅ tooling
- fase produto **v1.5** — proxima (a definir no roadmap)
- Camada prompts/Claude Projects + ativacao do piloto: **depende da Tia May** (claude.ai)

---

## Licenca

Apache-2.0 — herda do Claude for Legal upstream.

## Compliance

LGPD-first. **Nenhum dado real** em codigo, testes ou commits. Aprovacao
Tia May obrigatoria para mudancas em fluxo de dados.

Ver `docs/PII_GAPS.md` para decisoes de produto vs gaps reais de redacao.
