# LegalOps BR

Extensoes brasileiras sobre o **Claude for Legal** (Anthropic, Apache 2.0).

Sistema de processamento de intimacoes TJPR com gates LGPD: redacao PII →
parse → calculo CPC determinstico → audit chain SHA-256 → notificacao
WhatsApp. Local-first, **nenhuma chamada automatica a LLM externa**.

---

## Status v0.3

- **323/323 tests** passing, `mypy --strict` clean, `ruff` clean
- 100% recall + 100% precision por tipo PII (corpus 500 sintetico, 0 leaks)
- 8/8 cenarios pipeline E2E (dobro Fazenda, multiplos processos, multi-tribunal)
- Parsers: TJPR, TJSP, TJSC, TJRJ (detector via sender domain + header)
- PII v0.2: CPF/CNPJ sem mascara com modulo 11 (Receita Federal)
- 17+ commits master

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
| `cli` | argparse — `redact`, `parse`, `pipeline`, `batch`, `notify`, `audit` |

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

Ver `LegalOps — Roadmap.md` no vault Mafioso ou `docs/`:
- v0.1 PoC ✅
- v0.2 — gaps PII (CPF/CNPJ sem mascara — ver `docs/PII_GAPS.md`)
- v1.0 — Project 1 (Prazos) deploy + Tia May (30 dias producao limitada)
- v1.2 — Contract AI (commercial-legal plugin upstream)
- v1.3 — M&A + Due Diligence
- v1.4 — LGPD assistant

---

## Licenca

Apache-2.0 — herda do Claude for Legal upstream.

## Compliance

LGPD-first. **Nenhum dado real** em codigo, testes ou commits. Aprovacao
Tia May obrigatoria para mudancas em fluxo de dados.

Ver `docs/PII_GAPS.md` para decisoes de produto vs gaps reais de redacao.
