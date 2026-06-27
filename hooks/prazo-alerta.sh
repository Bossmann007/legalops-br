#!/usr/bin/env bash
# Alertas de prazo D-3 e D-1
# Cron: 0 9 * * 1-6 cd ~/Projects/legalops-br && ./hooks/prazo-alerta.sh >> logs/prazos.log 2>&1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source .env 2>/dev/null || true

# Verificar prazos por nível de urgência
uv run legalops prazos --vencendo-em 3 --format json 2>/dev/null | python3 - <<'PYEOF'
import json, sys, os

sys.path.insert(0, 'src')
from legalops.whatsapp_notifier import send_text

phone = os.environ.get('ADVOGADO_WHATSAPP', '')
if not phone:
    print('ERRO: ADVOGADO_WHATSAPP não configurado')
    sys.exit(1)

data = json.load(sys.stdin)
urgentes = [p for p in data if p.get('dias_restantes', 99) <= 1]
atencao = [p for p in data if 2 <= p.get('dias_restantes', 99) <= 3]

for p in urgentes:
    msg = (
        f"🔴 *PRAZO URGENTE — AMANHÃ*\n\n"
        f"Tipo: {p['tipo']}\n"
        f"Cliente: {p['cliente_alias']}\n"
        f"Vence: {p['data_final']}\n\n"
        f"_Protocolar hoje ou no máximo amanhã cedo._"
    )
    send_text(phone, msg)
    print(f"Alerta D-1 enviado: {p['tipo']} {p['cliente_alias']}")

if atencao and not urgentes:
    itens = '\n'.join([f"  • {p['tipo']} — {p['cliente_alias']} — {p['data_final']}" for p in atencao])
    msg = (
        f"🟡 *Prazos vencendo em 2–3 dias*\n\n"
        f"{itens}\n\n"
        f"_Use /briefing para detalhes._"
    )
    send_text(phone, msg)
    print(f"Alerta D-3 enviado: {len(atencao)} prazo(s)")
PYEOF
