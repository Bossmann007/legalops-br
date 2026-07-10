# Contributing to LegalOps BR

Obrigado pelo interesse. LegalOps BR e LGPD-first — qualquer mudanca
em fluxo de dados pessoais exige aprovacao explicita.

---

## Setup

```bash
git clone https://github.com/Bossmann007/legalops-br.git
cd legalops-br
uv venv --python 3.11
uv pip install -e ".[dev]"
uv run python corpus/synthetic/generate.py --count 200
uv run pytest
```

Apos install: `legalops --help` disponivel via entry point.

---

## Padroes do projeto

- **Python 3.11+** (StrEnum, tipo `X | None`)
- **`uv`** para deps (sem pip direto)
- **`ruff`** lint + format
- **`mypy --strict`** zero erros
- **`pytest`** todos verdes antes do PR
- **Sem deps externas em runtime** (stdlib preferido); `pydantic`,
  `python-dateutil`, `faker` ja sao as unicas

Pre-commit (manual ate ter pre-commit hooks):

```bash
uv run ruff check src tests scripts corpus
uv run mypy src
uv run pytest --no-cov
uv run python scripts/validate_pipeline.py
uv run python scripts/measure_redactor.py
```

---

## LGPD / PII — REGRAS ABSOLUTAS

1. **NUNCA** commite dados reais (CPF, CNPJ, RG, OAB, nomes de clientes,
   numeros de processo reais que possam identificar pessoa).
2. **SEMPRE** use placeholders sinteticos: `123.456.789-00`, `[OAB_REDACTED]`, etc.
3. **Audit log (`oab_sigilo`)** rejeita PII bruto em metadata — testes devem
   exercitar esse comportamento se mexerem no audit.
4. **Egress tests** (`tests/test_egress.py`) precisam passar com 0 leaks.
   Geram falsa-aprovacao se corpus nao for gerado. CI gera 200 docs antes
   dos testes — local idem.

---

## Adicionando novo PII pattern

1. Adicionar regex em `src/legalops/pii_redactor.py` (`PATTERNS` dict)
   ordenado por especificidade (longer/more-specific first).
2. Atualizar `tests/test_pii_redactor.py` com caso positivo + negativo.
3. Atualizar `corpus/synthetic/generate.py` se for util pra metricas.
4. Atualizar `docs/PII_GAPS.md` documentando decisao.
5. Rodar `uv run python scripts/measure_redactor.py` — recall deve subir
   ou manter, leak rate manter 0%.

---

## Adicionando novo agente Claude Project

Project 1 (Prazos) tem 7 agentes em `OneDrive/Mafioso/10 - Projetos/LegalOps/claude-projects-paste/`. Para novo agente:

1. Criar `agent-N-nome.txt` com system prompt completo.
2. Atualizar `SETUP.md` com Claude Project setup steps.
3. Atualizar `Project 1 — Prazos — Agent Prompts.md` (master doc).
4. Pipeline `Project 1 — Backend Pipeline.md` se mudar fluxo.

---

## Commit messages

Use imperativo + scope:

```
feat: redact CPF sem mascara via digito verificador
fix: cpc_prazos pula recesso TJPR no calculo
docs: PII_GAPS adiciona G4 (CEP)
test: orchestrator cobre fazenda via DJE
```

NAO commitar:
- `audit.db` / `audit_*.db`
- `corpus/synthetic/docs/` (regeneravel)
- Qualquer `.eml` com dados reais

`.gitignore` cobre — verificar `git status` antes.

---

## Pull requests

1. Branch a partir de `master`: `git checkout -b feat/nome-curto`
2. Fix + tests + docs
3. CI deve passar (GitHub Actions workflow `ci.yml`)
4. PR description menciona:
   - O que muda
   - Por que muda
   - Como testar
   - Impact LGPD/PII (se houver)

---

## Reportar vulnerabilidade

Email **enzombromanus@gmail.com** com `[SECURITY] LegalOps`.

NAO abra issue publica para vuln. 90 dias antes de disclosure publico.

---

## Codigo de conduta

[Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) — seja gentil, foque tecnicamente.

---

## Licenca

Apache-2.0 — ao contribuir voce concorda com a licenca do projeto.
