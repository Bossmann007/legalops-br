#!/usr/bin/env bash
# LegalOps — instalador do engine na máquina do escritório.
# Uso: bash setup.sh   (rode de dentro da pasta do projeto)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# --- #1 GUARD: nunca instalar dentro de pasta sincronizada (LGPD) ---------
# PII de cliente (data/, logs/, audit.db, memory.local/) fica nesta pasta.
# Sync de nuvem (OneDrive/Drive/Dropbox/iCloud) sobe esses arquivos mesmo
# gitignorados. Instalar sob pasta sincronizada = vazar dado de cliente.
case "$HERE" in
  *OneDrive*|*"Google Drive"*|*GoogleDrive*|*Dropbox*|*iCloud*|*"Library/Mobile Documents"*)
    echo "⛔ RECUSADO: LegalOps está numa pasta sincronizada com a nuvem:"
    echo "   $HERE"
    echo "   Dados de cliente vazariam para o serviço de nuvem (LGPD)."
    echo "   Mova para uma pasta LOCAL (ex: ~/legalops) e rode de novo."
    echo "   Para forçar mesmo assim (NÃO recomendado): SETUP_ALLOW_SYNC=1 bash setup.sh"
    [ "${SETUP_ALLOW_SYNC:-0}" = "1" ] || exit 1
    echo "   ⚠️  SETUP_ALLOW_SYNC=1 — prosseguindo por sua conta e risco."
    ;;
esac

# --- Python ---------------------------------------------------------------
command -v python3 >/dev/null 2>&1 || { echo "⛔ python3 não encontrado. Instale Python 3.11+."; exit 1; }

# --- Engine ---------------------------------------------------------------
if command -v uv >/dev/null 2>&1; then
  uv sync
else
  echo "⚠️  'uv' não encontrado — usando pip. (Recomendado: instale uv.)"
  python3 -m pip install -e .
fi

# --- Salt de PII (local, nunca sincronizado) ------------------------------
# Sem LEGALOPS_PII_SALT o CLI falha. Geramos um e gravamos em .env (gitignored).
if [ ! -f .env ] || ! grep -q "LEGALOPS_PII_SALT" .env 2>/dev/null; then
  SALT="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
  echo "LEGALOPS_PII_SALT=$SALT" >> .env
  echo "🔑 Salt de PII gerado em .env (não versionado, não sincronize)."
fi

echo
echo "✅ LegalOps instalado."
echo "   Próximo passo: abra o Claude Code aqui e rode  /onboarding"
