#!/usr/bin/env bash
# deploy/setup.sh — Instalação permanente do Maffini Dashboard via systemd
# Uso: sudo bash deploy/setup.sh [--dest /caminho/opcional]
set -euo pipefail

# ── Cores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }

# ── Root check ─────────────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || error "Execute como root: sudo bash deploy/setup.sh"

# ── Parâmetros ─────────────────────────────────────────────────────────────
DEST=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --dest) DEST="$2"; shift 2 ;;
    *) error "Opção desconhecida: $1" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")"

if [[ -z "$DEST" ]]; then
  read -rp "Caminho de instalação [/opt/maffini-dashboard]: " DEST
  DEST="${DEST:-/opt/maffini-dashboard}"
fi

SERVICE_NAME="maffini-dashboard"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
UNIT_SRC="$SCRIPT_DIR/${SERVICE_NAME}.service"

# ── Pré-requisitos ─────────────────────────────────────────────────────────
command -v node >/dev/null || error "Node.js não encontrado. Instale Node 20+: https://nodejs.org"
NODE_MAJOR=$(node --version | sed 's/v\([0-9]*\).*/\1/')
[[ $NODE_MAJOR -ge 20 ]] || error "Node.js 20+ obrigatório (encontrado: v${NODE_MAJOR})"
command -v npm >/dev/null || error "npm não encontrado"
info "Node.js $(node --version) OK"

# ── Copiar arquivos ────────────────────────────────────────────────────────
info "Copiando para $DEST..."
mkdir -p "$DEST"
rsync -a --exclude='.env' --exclude='node_modules' --exclude='data' \
  "$SRC_DIR/" "$DEST/"

# ── npm install + build ────────────────────────────────────────────────────
info "Instalando dependências npm..."
cd "$DEST"
npm install --omit=dev --silent
info "Buildando assets..."
npm run build --silent

# ── .env ──────────────────────────────────────────────────────────────────
if [[ ! -f "$DEST/.env" ]]; then
  warn ".env não encontrado. Criando a partir de .env.example..."
  cp "$DEST/.env.example" "$DEST/.env"
  chmod 600 "$DEST/.env"

  SALT=$(node -e "const c=require('crypto');console.log(c.randomBytes(24).toString('hex'))")
  sed -i "s|^LEGALOPS_PII_SALT=.*|LEGALOPS_PII_SALT=${SALT}|" "$DEST/.env"
  info "LEGALOPS_PII_SALT gerado automaticamente."
  warn "IMPORTANTE: edite $DEST/.env e preencha LEGALOPS_BIN com o caminho do legalops."
else
  info ".env já existe — mantendo sem alteração."
fi
chmod 600 "$DEST/.env"

# ── data dir ──────────────────────────────────────────────────────────────
mkdir -p "$DEST/data"

# ── Usuário de serviço ────────────────────────────────────────────────────
SVC_USER="maffini"
if ! id "$SVC_USER" &>/dev/null; then
  info "Criando usuário de sistema '$SVC_USER'..."
  useradd --system --no-create-home --shell /usr/sbin/nologin "$SVC_USER"
fi
chown -R "$SVC_USER:$SVC_USER" "$DEST"

# ── systemd unit ──────────────────────────────────────────────────────────
info "Instalando unit systemd..."
[[ -f "$UNIT_SRC" ]] || error "Unit file não encontrado em $UNIT_SRC"

NODE_BIN="$(command -v node)"
sed \
  -e "s|WorkingDirectory=.*|WorkingDirectory=${DEST}|" \
  -e "s|EnvironmentFile=.*|EnvironmentFile=${DEST}/.env|" \
  -e "s|ExecStart=.*|ExecStart=${NODE_BIN} ${DEST}/server/index.js|" \
  "$UNIT_SRC" > "$SERVICE_FILE"

chmod 644 "$SERVICE_FILE"

# ── Habilitar e iniciar ────────────────────────────────────────────────────
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

# ── Health check ──────────────────────────────────────────────────────────
sleep 2
PORT=$(grep -E '^MAFFINI_PORT=' "$DEST/.env" 2>/dev/null | cut -d= -f2)
PORT="${PORT:-4318}"
HOST=$(grep -E '^MAFFINI_HOST=' "$DEST/.env" 2>/dev/null | cut -d= -f2)
HOST="${HOST:-127.0.0.1}"

if curl -sf "http://${HOST}:${PORT}/api/health" >/dev/null 2>&1; then
  info "Health check OK — dashboard respondendo."
else
  warn "Health check falhou — verifique o .env e os logs:"
  warn "  journalctl -u ${SERVICE_NAME} -n 30"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Instalado em: ${DEST}${NC}"
echo -e "${GREEN}  Abra no navegador: http://localhost:${PORT}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  status : systemctl status ${SERVICE_NAME}"
echo "  parar  : sudo systemctl stop ${SERVICE_NAME}"
echo "  logs   : journalctl -u ${SERVICE_NAME} -f"
echo "  config : \$EDITOR ${DEST}/.env && sudo systemctl restart ${SERVICE_NAME}"
echo ""
if grep -qE '^LEGALOPS_BIN=$' "$DEST/.env" 2>/dev/null; then
  warn "Pendente: edite $DEST/.env e defina LEGALOPS_BIN antes de usar."
fi
