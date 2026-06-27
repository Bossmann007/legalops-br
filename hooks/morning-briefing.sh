#!/usr/bin/env bash
# Morning briefing — prazos urgentes às 7h via WhatsApp
# Cron: 0 7 * * 1-6 cd ~/Projects/legalops-br && ./hooks/morning-briefing.sh >> logs/briefing.log 2>&1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source .env 2>/dev/null || true

DATE=$(date +%Y-%m-%d)
DAY=$(date +"%A, %d/%m")

# Prazos urgentes (vencendo em até 3 dias úteis)
PRAZOS=$(uv run legalops prazos --vencendo-em 3 --format json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not data:
    print('Nenhum prazo urgente.')
else:
    for p in data[:5]:
        urgencia = '🔴' if p['dias_restantes'] <= 1 else '🟡'
        print(f'  {urgencia} {p[\"tipo\"]} — {p[\"cliente_alias\"]} — vence {p[\"data_final\"]}')
" 2>/dev/null || echo "  Sem dados de prazo disponíveis")

# Processos com movimentação hoje
MOVIMENTACOES=$(uv run legalops processos --movimentacao-hoje --format json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not data:
    print('')
else:
    lines = [f'  📋 {p[\"tribunal\"]} — {p[\"tipo_movimentacao\"]}' for p in data[:3]]
    print('\n'.join(lines))
" 2>/dev/null || echo "")

# Montar mensagem
MSG="⚖️ *Bom dia!*
*$DAY*

📅 *Prazos urgentes:*
$PRAZOS"

if [ -n "$MOVIMENTACOES" ]; then
MSG="$MSG

🔔 *Processos com novidade:*
$MOVIMENTACOES"
fi

MSG="$MSG

_Use /briefing para detalhes completos._ 📋"

# Enviar via whatsapp_notifier
python3 -c "
import sys, os
sys.path.insert(0, 'src')
from legalops.whatsapp_notifier import send_text
phone = os.environ.get('ADVOGADO_WHATSAPP', '')
if not phone:
    print('ERRO: ADVOGADO_WHATSAPP não configurado no .env')
    sys.exit(1)
send_text(phone, '''$MSG''')
print('Briefing enviado para', phone)
"
