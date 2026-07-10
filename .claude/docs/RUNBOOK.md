# LegalOps BR — Operational Runbook

> Deploy + ops guide for production pilot.

## Pre-requisitos

| Componente | Versao | Necessidade |
|------------|--------|-------------|
| Python | 3.11+ | Runtime |
| uv | 0.5+ | Build/deps |
| systemd | qualquer | Timer/service (Linux) |

## Deploy local (dev/pilot)

```bash
cd ~/Projects/legalops-br
uv sync
export LEGALOPS_PII_SALT="$(openssl rand -hex 24)"  # obrigatorio; guardar em secret manager
uv run pytest -q --no-cov   # esperar 844/844
uv run mypy --strict src/    # 0 errors
uv run ruff check .          # 0 errors
uv run legalops --help
```

## Config TOML (opcional)

Defaults por subcomando, lidos por `legalops/config.py` de `~/.config/legalops/config.toml`
se o arquivo existir (ausente = usa defaults internos). Copie o exemplo e ajuste:

```bash
mkdir -p ~/.config/legalops
cp legalops.toml.example ~/.config/legalops/config.toml   # editar tribunal/parte
```

```toml
[defaults]
parte = "particular"   # particular | fazenda | mp | defensoria
via_dje = false
tribunal = "TJPR"
```

Flag CLI sempre vence o config: `legalops prazo --parte fazenda` ignora `defaults.parte`.

## Pipeline E2E

```bash
# 1. Manual single email
echo "..." | legalops pipeline --audit-db audit.db

# 2. Batch directory
legalops batch --dir ./inbox --audit-db audit.db

```

## Monitoramento

```bash
# Audit log integrity
legalops audit verify --db ~/.local/share/legalops/audit.db

# Recent entries
legalops audit list --db ~/.local/share/legalops/audit.db | jq

# Metrics
ls -lt metrics/ | head
cat metrics/metrics_$(date +%Y%m%d).json | jq .recall_by_type
```

## Pre-release checklist

- [ ] `export LEGALOPS_PII_SALT="$(openssl rand -hex 24)"` (obrigatorio antes de scripts/CLI que tocam PII)
- [ ] `uv run pytest -q --no-cov` → 811+ pass
- [ ] `uv run mypy --strict src/` clean
- [ ] `uv run ruff check .` clean
- [ ] `uv run python scripts/measure_redactor.py` → recall ≥ 0.95 + leaks=0
- [ ] `uv run python scripts/validate_pipeline.py` → 8/8 OK
- [ ] `uv run python scripts/benchmark_pipeline.py` → ms/doc baseline
- [ ] Audit chain verifica: `legalops audit verify --db audit.db`

## Incidentes

### "Recall caiu em prod"
1. Verifica corpus drift: novos padroes nao cobertos
2. Adiciona pattern em `pii_redactor.py` (rebuild required)
3. Regenera corpus + re-run `measure_redactor.py`

### "Vazamento PII detectado"
**BLOQUEAR DEPLOY**. Investiga:
1. `grep -r '\d{3}\.\d{3}\.\d{3}-\d{2}' /var/log/legalops/` (NAO deveria existir)
2. Identifica path: redactor sequencia, audit log, network egress
3. Rollback imediato. Patch + verify `test_egress.py` cobre case.

### "Audit chain broken"
1. `legalops audit verify --db audit.db` retorna fail
2. Investiga tamper. Compara hash chain manualmente:
   ```python
   from legalops.oab_sigilo import AuditLog
   log = AuditLog(Path("audit.db"))
   print(log.verify_chain())  # bool + dict erros
   ```
3. NAO use audit_db corrompido em legalops downstream.

## LGPD compliance (resumo)

- Toda redacao usa SHA-256 salted (NAO reversivel)
- Audit log rejeita PII em metadata via regex pre-insert
- Nenhuma chamada externa a LLM sem aprovacao Tia May (copy-paste manual)
- Egress segue [SECURITY.md](SECURITY.md), seção "Egress / vazamento de PII — postura em camadas"

## Contatos

| Issue | Responsavel | Canal |
|-------|-------------|-------|
| Bug parser/CPC | Enzo | GitHub Issues `Bossmann007/legalops-br` |
| LGPD review | Tia May | Email |
