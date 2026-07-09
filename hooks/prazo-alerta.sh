#!/usr/bin/env bash
# DEPRECATED no piloto: notificação agora é PULL — a advogada abre o Claude e roda
# /briefing ou /painel. Sem push WhatsApp. Script dormente (canal opcional); não wire em cron.
# Alertas de prazo D-3/D-1 — envio deliberado para WhatsApp configurado.
# --approved = decisão consciente de enviar mensagem fora do fluxo interativo.
# Cron: 0 9 * * 1-6 cd ~/Projects/legalops-br && ./hooks/prazo-alerta.sh >> logs/prazos.log 2>&1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source .env 2>/dev/null || true

INPUT="${LEGALOPS_NOTIFY_INPUT:-data/intimacoes.txt}"
if [ ! -f "$INPUT" ]; then
  echo "Sem input de intimacoes em $INPUT; nada a enviar."
  exit 0
fi

if [ -z "${ADVOGADO_WHATSAPP:-}" ]; then
  echo "ERRO: ADVOGADO_WHATSAPP não configurado no .env"
  exit 1
fi

uv run legalops notify \
  --input "$INPUT" \
  --chat-id "$ADVOGADO_WHATSAPP" \
  --hoje "$(date +%Y-%m-%d)" \
  --approved
