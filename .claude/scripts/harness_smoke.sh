#!/usr/bin/env bash
# Harness smoke — valida a camada cliente (hooks/agents/manifest), não o engine Python.
# Espelho scoped do ~/.claude/hooks/tests/harness-smoke.sh pessoal.
# Roda no CI e no pre-commit. Falha fechada: qualquer erro → exit 1.
set -euo pipefail
cd "$(dirname "$0")/../.."

fail=0
check() { if "$@"; then echo "  ok: $*"; else echo "  FAIL: $*"; fail=1; fi; }

echo "[1] JSON válido — settings.json + memory-manifest.json"
for j in .claude/settings.json .claude/memory-manifest.json; do
  if python -c "import json,sys; json.load(open('$j'))" 2>/dev/null; then
    echo "  ok: $j"
  else
    echo "  FAIL: $j inválido"; fail=1
  fi
done

echo "[2] Hooks referenciados existem"
python - <<'PY' || fail=1
import json, re, os, sys
cfg = json.load(open(".claude/settings.json"))
missing = []
for evs in cfg.get("hooks", {}).values():
    for group in evs:
        for h in group.get("hooks", []):
            for m in re.findall(r'\$(?:\{)?CLAUDE_PROJECT_DIR(?:\})?/([^\s"\\]+\.(?:mjs|js|sh|md))', h.get("command","")):
                if ".local" in m:  # override local opcional (gitignored, tem fallback ||)
                    continue
                if not os.path.exists(m):
                    missing.append(m)
if missing:
    print("  FAIL: hooks apontam p/ arquivos inexistentes:", missing); sys.exit(1)
print("  ok: todos os hook targets existem")
PY

echo "[3] Agents sem import morto (módulo legalops inexistente)"
python - <<'PY' || fail=1
import re, os, glob, sys
dead = []
for f in glob.glob(".claude/agents/*.md"):
    txt = open(f).read()
    for mod in re.findall(r'(?:from|import)\s+legalops\.([a-z_]+)', txt):
        if not os.path.exists(f"src/legalops/{mod}.py"):
            dead.append(f"{f}: legalops.{mod}")
if dead:
    print("  FAIL: import morto em agents:", dead); sys.exit(1)
print("  ok: nenhum import morto em agents/")
PY

echo "[4] Anti-injection scanner (test.mjs)"
if command -v node >/dev/null; then
  check node .claude/anti-injection/hooks/test.mjs
else
  echo "  SKIP: node ausente"
fi

echo "[5] Sem path pessoal absoluto em arquivos versionados"
# path /home/<user> hardcoded vaza path pessoal e quebra no clone da advogada.
# Hooks/comandos/scripts devem usar \$CLAUDE_PROJECT_DIR ou ~/legalops.
# Needle montado por partes p/ este arquivo nao casar a si mesmo.
NEEDLE="$(printf '/home/%s' bossmann)"
if git grep -nI "$NEEDLE" -- . >/dev/null 2>&1; then
  echo "  FAIL: path pessoal hardcoded (use \$CLAUDE_PROJECT_DIR ou ~/legalops):"
  git grep -nI "$NEEDLE" -- .
  fail=1
else
  echo "  ok: nenhum path pessoal versionado"
fi

if [ "$fail" -ne 0 ]; then echo "HARNESS SMOKE: FALHOU"; exit 1; fi
echo "HARNESS SMOKE: OK"
