# LegalOps BR — Operational Runbook

> Deploy + ops guide for production pilot.

## Pre-requisitos

| Componente | Versao | Necessidade |
|------------|--------|-------------|
| Python | 3.11+ | Runtime |
| uv | 0.5+ | Build/deps |
| systemd | qualquer | Timer/service (Linux) |
| WhatsApp bridge.js | qualquer | Notificacoes (porta 3000) |
| GalileuCLI | 1.0+ | Proxy MITM opcional (porta 9000) |

## Deploy local (dev/pilot)

```bash
cd ~/Projects/legalops-br
uv sync
export LEGALOPS_PII_SALT="$(openssl rand -hex 24)"  # obrigatorio; guardar em secret manager
uv run pytest -q --no-cov   # esperar 763/763
uv run mypy --strict src/    # 0 errors
uv run ruff check .          # 0 errors
mkdir -p ~/.config/legalops ~/.local/share/legalops
cp legalops.toml.example ~/.config/legalops/config.toml   # ajustar
ln -s "$PWD"/.venv/bin/legalops ~/.local/bin/legalops
legalops --help
```

## Deploy via Docker

```bash
docker build -t legalops:0.3 .
docker run --rm -v "$PWD"/data:/data legalops:0.3 \
    pipeline --input /data/email.txt --audit-db /data/audit.db
```

## Config TOML

`~/.config/legalops/config.toml`:

```toml
[defaults]
parte = "particular"
via_dje = false
tribunal = "TJPR"

[audit]
db = "~/.local/share/legalops/audit.db"

[whatsapp]
chat_id = "5541999999999@s.whatsapp.net"
bridge_url = "http://localhost:3000"
timeout = 10.0
```

Override via flag CLI: `legalops pipeline --parte fazenda` ignora `defaults.parte`.

## Pipeline E2E

```bash
# 1. Manual single email
echo "..." | legalops pipeline --audit-db audit.db

# 2. Batch directory
legalops batch --dir ./inbox --audit-db audit.db

# 3. Notify urgentes via WhatsApp
legalops notify --input email.txt --chat-id "$WA_CHAT_ID" --audit-db audit.db

# 4. Notify multi-channel (v1.3)
legalops notify -i email.txt --channels whatsapp,email,slack \
  --min-prazo-days 3 --quiet-start 22:00 --quiet-end 06:00
```

## Multi-channel notifications (v1.3)

Tres canais suportados, configurados via `~/.config/legalops/config.toml`:

```toml
[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
username = "ops@firma.com"
password = "app-password"      # use Gmail App Password, nao senha real
from_addr = "ops@firma.com"
to_addr = "advogado@firma.com"
use_tls = true

[slack]
webhook_url = "https://hooks.slack.com/services/T/B/X"
channel = "#prazos"            # opcional

[notification]
channels = ["whatsapp", "email", "slack"]
min_prazo_days = 3             # so notifica prazos <= N dias uteis
quiet_start = "22:00"          # silencia janela (24h ok via meia-noite)
quiet_end = "06:00"
```

Gmail: gere App Password em https://myaccount.google.com/apppasswords.
Slack: crie incoming webhook em https://api.slack.com/messaging/webhooks.

LGPD: mensagens em todos os canais contem apenas `numero_processo` + `dies_ad_quem` +
`prazo_efetivo_dias`. Sem nomes, CPFs, conteudo de ato.

Falha de um canal nao quebra outros — multiplex loga e segue.

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
- [ ] `uv run pytest -q --no-cov` → 763+ pass
- [ ] `uv run mypy --strict src/` clean
- [ ] `uv run ruff check .` clean
- [ ] `uv run python scripts/measure_redactor.py` → recall ≥ 0.95 + leaks=0
- [ ] `uv run python scripts/validate_pipeline.py` → 8/8 OK
- [ ] `uv run python scripts/benchmark_pipeline.py` → ms/doc baseline
- [ ] Audit chain verifica: `legalops audit verify --db audit.db`
- [ ] Galileu doctor OK: `~/Projects/galileu-cli/galileu doctor`
- [ ] Bridge.js WhatsApp responde: `curl -X POST localhost:3000/send -d '{"chatId":"...","message":"test"}'`

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
- Galileu proxy (opcional) adiciona camada network defense-in-depth
- Bridge WhatsApp formata mensagens sem PII (apenas CNJ + dies ad quem)

## Contatos

| Issue | Responsavel | Canal |
|-------|-------------|-------|
| Bug parser/CPC | Enzo | GitHub Issues `Bossmann007/legalops-br` |
| LGPD review | Tia May | Email |
| Infra (bridge/Galileu) | Enzo | Local |
