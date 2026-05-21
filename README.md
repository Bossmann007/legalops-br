# LegalOps BR

Extensoes brasileiras sobre o **Claude for Legal** (Anthropic, Apache 2.0).

## Componentes v0.1 PoC

- **`pii-redactor-br`** — Detecta e mascara CPF, CNPJ, RG, OAB, PIX, email, telefone BR antes de enviar texto a LLMs.
- **`corpus/synthetic`** — Gerador de documentos sinteticos para testar redaction sem PII real.
- **`tests/egress`** — Testa que dados brutos NUNCA saem da maquina local.
- **`proxy/galileu`** — Configuracao GalileuCLI (proxy local Go) para egress control no nivel network.

## Stack

- Python 3.11+
- uv (gestor)
- pytest + ruff + mypy strict
- GalileuCLI (Go, https://github.com/eubrunocase/GalileuCLI)

## Setup

```bash
uv venv --python 3.11
uv pip install -e ".[dev]"
uv run pytest
```

## Roadmap

Ver LegalOps Roadmap no vault Mafioso.

## Licenca

Apache-2.0 — herda do Claude for Legal upstream.

## Compliance

LGPD-first. Nenhum dado real em codigo, testes ou commits. Aprovacao Tia May obrigatoria para mudancas em fluxo de dados.
