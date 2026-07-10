# LegalOps — instalador do engine no Windows (PowerShell).
# Uso: no PowerShell, dentro da pasta do projeto:  .\setup.ps1
# Se o PowerShell bloquear scripts, rode antes:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$ErrorActionPreference = "Stop"

$Here = $PSScriptRoot
Set-Location $Here

# --- #1 GUARD: nunca instalar dentro de pasta sincronizada (LGPD) ---------
# PII de cliente (data\, logs\, audit.db, memory.local\) fica nesta pasta.
# Windows 11 sincroniza Documentos/Desktop pro OneDrive por padrao — instalar
# ai sobe dado de cliente pra nuvem. Use uma pasta LOCAL (ex: C:\legalops).
$SyncPatterns = @("OneDrive", "Google Drive", "GoogleDrive", "Dropbox", "iCloudDrive", "iCloud")
$Synced = $SyncPatterns | Where-Object { $Here -like "*$_*" }
if ($Synced) {
    Write-Host "RECUSADO: LegalOps esta numa pasta sincronizada com a nuvem:" -ForegroundColor Red
    Write-Host "   $Here"
    Write-Host "   Dados de cliente vazariam para o servico de nuvem (LGPD)."
    Write-Host "   Mova para uma pasta LOCAL (ex: C:\legalops) e rode de novo."
    Write-Host "   Para forcar mesmo assim (NAO recomendado): `$env:SETUP_ALLOW_SYNC=1; .\setup.ps1"
    if ($env:SETUP_ALLOW_SYNC -ne "1") { exit 1 }
    Write-Host "   SETUP_ALLOW_SYNC=1 — prosseguindo por sua conta e risco." -ForegroundColor Yellow
}

# --- Python (aceita 'python' ou 'python3'; PowerShell 5.1+ compat) ---------
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $Python) { Write-Host "Python nao encontrado. Instale Python 3.11+ (python.org ou Microsoft Store)." -ForegroundColor Red; exit 1 }
$Py = $Python.Source

# --- Engine ---------------------------------------------------------------
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv sync
} else {
    Write-Host "'uv' nao encontrado — usando pip. (Recomendado: instale uv.)" -ForegroundColor Yellow
    & $Py -m pip install -e .
}

# --- Salt de PII (local, nunca sincronizado) ------------------------------
# Sem LEGALOPS_PII_SALT o CLI falha. Geramos um e gravamos em .env (gitignored).
$HasSalt = (Test-Path .env) -and (Select-String -Path .env -Pattern "LEGALOPS_PII_SALT" -Quiet)
if (-not $HasSalt) {
    $Salt = & $Py -c "import secrets; print(secrets.token_hex(24))"
    Add-Content -Path .env -Value "LEGALOPS_PII_SALT=$Salt"
    Write-Host "Salt de PII gerado em .env (nao versionado, nao sincronize)."
}

Write-Host ""
Write-Host "LegalOps instalado." -ForegroundColor Green
Write-Host "   Proximo passo: abra o Claude Code aqui e rode  /onboarding"
