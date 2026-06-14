# Changelog — Maffini Dashboard

## [0.1.0] — 2026-06-14

### Adicionado
- Centro de comando com 9 módulos: Home · Prazos · Intimações · Contratos · DSAR · Clientes · Audit · Config · Comandos
- Pipeline de intimações com redação PII automática (LGPD Art. 13), cálculo de prazo e audit trail
- Análise de risco contratual via Claude for Legal (opt-in, requer `ANTHROPIC_API_KEY`)
- Gestão de DSARs com prazo legal de 15 dias calculado automaticamente
- Hash chain de integridade em todas as operações de auditoria
- Approval gate por comando: modal confirm + 403 server-side (`approved !== true` → bloqueado)
- Boot guard: servidor recusa iniciar sem auth em interfaces não-loopback
- Mini CRM de clientes (aliases pseudonimizados)
- Gestão de prazos processuais com destaque para vencimentos em 7 dias
- Tema visual teal `#388da5` + Manrope — identidade Maffini & Rangel
- Deploy: unit systemd com hardening (`NoNewPrivileges`, `PrivateTmp`, `ProtectSystem`)
- 50 testes automatizados (100% pass)
- Guia de instalação em português (`INSTALL.md`)
- Script de deploy one-shot (`deploy/setup.sh`) com caminho configurável

### Segurança
- Pseudonimização PII com HMAC-SHA256 antes de qualquer processamento externo
- Redação obrigatória via `legalops redact` antes de egress para Anthropic API
- `.env` com `chmod 600` automático no setup
- Loopback-only sem auth — impossível expor sem credenciais em LAN/WAN

### Pendente (v0.2)
- Templates `.docx` para peças processuais
- Notificações WhatsApp / email / Slack
- Ingest automático M365 (Outlook intimações)
- Calendário `.ics` export
