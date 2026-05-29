# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ active |
| 0.x     | ❌ end-of-life |

## Reporting a Vulnerability

Vulnerabilities devem ser reportadas privadamente — **nao abra GitHub issue publico**.

**Contato:** enzombromanus@gmail.com (PGP key on request)

**Inclua:**
- Descricao tecnica
- Steps to reproduce (preferencialmente com PoC sintetico — SEM PII real)
- Impact assessment (confidencialidade/integridade/disponibilidade)
- Versao afetada

**SLA:**
- Acknowledge: 48h
- Triage: 7 dias
- Fix critical/high: 14 dias
- Disclosure coordenada apos patch release

## Security Posture

### Dados sensiveis (LGPD)

- **PII em logs:** PROIBIDO. `oab_sigilo` regex rejeita pre-insert
- **PII em metadata audit:** PROIBIDO. `PIIInAuditError` raised
- **PII em mensagens WhatsApp:** PROIBIDO. Formato fixo `{numero_processo, dies_ad_quem}`
- **PII em URL params:** PROIBIDO. Todo PII via body POST
- **PII bruto em cache/disco:** PROIBIDO. Apenas SHA-256 salted

### Cryptographic posture

- SHA-256 com salt customizavel (default `legalops-br-v0.1`) pra hash de PII
- Salt configuravel via env/config — recomenda rotacao em deploy
- Sem reversibilidade — auditoria via hash matching apenas

### Network posture

- Stdlib `urllib` apenas (sem httpx — reduzir surface attack)
- M365 OAuth: token cache em memoria (nao persistido)
- M365: HTTPS enforced (urllib default)
- GalileuCLI (opcional, Go MITM proxy :9000) adiciona network gate

### Audit log posture

- SQLite com `BEGIN IMMEDIATE` atomic transactions
- SHA-256 chain (cada entry referencia hash do anterior)
- Tamper-detection via `verify_chain()`
- JSON deterministico (`sort_keys=True`) pra reprodutibilidade

### CI/CD posture

- Pre-commit hooks: ruff, mypy, pytest, detect-private-key, no-real-pii
- `detect-private-key` bloqueia `.pem`, `.key`, SSH keys staged
- `no-real-pii` blocks reserved names no diff via printf-broken regex pattern
- GitHub Actions runs full suite + measure_redactor + validate_pipeline

## Threat Model

### In-scope

- Acidental PII leak via logs, errors, metadata, audit, network
- Tampering com audit log
- False negative em PII detection (pattern drift)
- Token theft (M365 cache poisoning)

### Out-of-scope

- Compromise do bridge.js WhatsApp (depende projeto externo)
- Compromise da Microsoft Graph API (depende Microsoft)
- Compromise do Galileu proxy (depende projeto externo)
- Side-channel attacks (timing, memory) em vulneravel hardware

## Hall of Fame

(Reports first responsibly disclosed land here.)
