# LegalOps BR — Code Review (sessão 2026-05-23)

> **Para o Claude na próxima sessão:** leia este arquivo antes de implementar mudanças.
> Escopo da revisão: **todo o repositório exceto** `slide/legalops_pptx.js` (slides não devem ser alterados salvo pedido explícito).

---

## Estado geral

| Área | Status |
|------|--------|
| Testes | **212 passed**, ~91% cobertura em `src/legalops` |
| `mypy --strict` | **2 erros** em `eml_reader.py` e `cli.py` |
| `ruff` | **21 avisos** (maioria estilo; alguns relevantes) |
| CI | **Não há** workflow em `.github/workflows/` |
| Corpus sintético | **`corpus/synthetic/docs/` vazio** — testes de egress fazem `pytest.skip` sem gerar corpus |

O núcleo Python (redactor → parser → prazos → orchestrator → audit) está sólido para PoC v0.1.

---

## Erros / inconsistências reais

### 1. `scripts/validate_pipeline.py` não testa o que o comentário diz

O email "Sentença contra Fazenda (dobro)" chama `calcular_prazo` sempre com `parte="particular"` (linha ~94). O dobro da Fazenda (Art. 183) **nunca é exercitado** nesse script.

Além disso, o script **duplica** a lógica do `orchestrator` em vez de chamar `process_email()` — risco de drift entre validação E2E e produção.

### 2. Critério de sucesso fraco no `validate_pipeline.py`

```python
if total_sucesso < len(SYNTHETIC_EMAILS) - 1:
    return 1
```

Permite **1 falha em 4** emails e ainda exit code 0. Permissivo demais para validação de pipeline.

### 3. `mypy --strict` falha (pyproject declara strict)

| Arquivo | Problema |
|---------|----------|
| `src/legalops/eml_reader.py:77` | `Message` sem `get_content` no tipo (mypy sugere `get_content_type`) |

### 4. Lacunas de PII (alinhar com discurso LGPD do produto)

| Gap | Impacto |
|-----|---------|
| CPF/CNPJ **sem máscara** (`12345678900`) | Não redigidos pelos regex atuais |
| **Número CNJ** no texto | Mantido de propósito para o parser; também vai para `audit` `resource` |
| `oab_sigilo` audit | Só bloqueia CPF/CNPJ/RG no metadata — **email, OAB, telefone** passam |

Não é bug se for decisão de produto — documentar na proposta/LGPD.

### 5. `pyproject.toml` incompleto

- Sem **`[project.scripts]`** — não existe comando `legalops` após install; só `python -m legalops.cli`.
- **`faker`** só em `dev`, mas `corpus/synthetic/generate.py` importa `Faker` em runtime.
- Sem **`.env.example`** (regra de segurança do projeto pede placeholder).

### 6. Higiene do repositório

- **`slide/node_modules/`** e **`slide/package.json`** — não estão no `.gitignore`; risco de commit acidental.
- **`metrics/*.json`** versionado — pode ficar desatualizado vs código.

### 7. Sem CI

Sem GitHub Actions, ninguém garante `pytest` / `ruff` / `mypy` antes de merge. Job precisa gerar corpus (`corpus/synthetic/generate.py`) antes dos testes de egress.

---

## Pontos fortes (manter)

- **`orchestrator.py`** — pipeline claro, audit opcional, erros por intimação.
- **`oab_sigilo.py`** — cadeia SHA-256, SQLite transacional, guarda PII no metadata.
- **`cpc_prazos.py`** — feriados, recesso TJPR, dobro por parte, alertas; bem testado.
- **`pii_redactor.py`** — placeholders determinísticos, ordem por especificidade.
- **`cli.py`** — `redact`, `parse`, `pipeline`, `batch`, `audit`.

---

## Melhorias recomendadas (prioridade)

### Alta

1. Unificar `scripts/validate_pipeline.py` com `process_email()`; testar `parte="fazenda"` no caso certo.
2. Corrigir os 2 erros de `mypy`.
3. `.gitignore`: `slide/node_modules/`, `slide/package-lock.json` (se existir).
4. Documentar ou fechar gaps de PII (CNJ, CPF sem máscara, audit ampliado).

### Média

5. `[project.scripts]` → `legalops = "legalops.cli:main"`.
6. CI mínimo: `uv sync` → gerar corpus → `pytest` → `ruff check` → `mypy src`.
7. Atualizar **README** (faltam orchestrator, CLI, LGPD, feeds, practice profile).
9. `eml_reader.read_eml_dir` — documentar não-recursivo; considerar limite de arquivos.

### Baixa

10. Ruff: `StrEnum` em vez de `str, Enum`; E501 em `lgpd_specifics.py`.
11. `bacen_cvm_feeds`: `defusedxml` se aceitar XML de rede no futuro (hoje stub).
12. `AGENTS.md` ou `CONTRIBUTING.md` — setup e corpus.

---

## Scripts e testes

| Arquivo | Observação |
|---------|------------|
| `scripts/measure_redactor.py` | Boa métrica recall/leak; depende do corpus gerado |
| `tests/test_egress.py` | **Skip** sem corpus — clone fresco parece verde sem testar egress |
| `corpus/synthetic/generate.py` | Ruff S311 em `random` — OK para dados fake |

---

## Slides (referência apenas — não alterar sem pedido)

Arquivo: `slide/legalops_pptx.js` — revisão feita em sessão anterior; usuário pediu **não corrigir slides**. Problemas conhecidos lá incluem typo EOAB→OAB, custos contraditórios entre slides, numeração de comentários duplicada, path OneDrive hardcoded, falta de `package.json` para pptxgenjs. Ver histórico da conversa se necessário.

---

## Comandos úteis para revalidar

```bash
cd ~/legalops
uv run pytest
uv run ruff check src tests scripts corpus
uv run mypy src
python corpus/synthetic/generate.py --count 200 --out corpus/synthetic/docs/
uv run python scripts/validate_pipeline.py
uv run python scripts/measure_redactor.py
```

---

## Conclusão

Código Python do PoC está em bom estado; gaps principais são **tooling** (mypy, CI, entry point), **validate_pipeline desalinhado**, **PII/documentação** e **git hygiene** (`slide/node_modules`).
