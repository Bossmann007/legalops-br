# Maffini Dashboard

> Centro de comando da Tia May (Maffini & Rangel — Advogados Associados).
> UI personalizada sobre [legalops-br](https://github.com/Bossmann007/legalops-br) — prazos processuais, inbox de intimações, contratos, DSAR LGPD, audit trail.

**Stack:** Node.js 20+ · zero runtime deps · HTTP nativo · vanilla JS · CSS variables · `node --test`.

**Inspirado em:** [`agentic-os`](https://github.com/Bossmann007/agentic-os) — mesma arquitetura (concat build, route registry, .env loader sem dep), brand-first jurídico em vez de dev-glass-dark.

---

## Setup

### 1. Pré-requisitos

- Node.js 20+ (`node --version`)
- LegalOps instalado e em `$PATH` (ou setar `LEGALOPS_BIN`)
- Python 3.11+ (vem com legalops)

### 2. Clone + instalar

```bash
git clone git@github.com:Bossmann007/maffini-dashboard.git
cd maffini-dashboard
# Sem npm install — não há deps de runtime.
cp .env.example .env
chmod 600 .env
$EDITOR .env  # preencher MAFFINI_AUTH_USER, MAFFINI_AUTH_PASS, LEGALOPS_PII_SALT
```

### 3. Gerar salt secreto LGPD (Art. 13)

```bash
echo "LEGALOPS_PII_SALT=$(openssl rand -hex 24)" >> .env
```

### 4. Gerar hash de senha admin (recomendado em prod)

```bash
node -e "console.log(require('./server/lib/auth').hashPassword('MINHA_SENHA'))"
# copie a saída scrypt$… para MAFFINI_AUTH_PASS_HASH no .env
```

Em dev você pode usar `MAFFINI_AUTH_PASS=plaintext`, mas em prod use sempre o hash.

### 5. Bootar

```bash
npm run build   # concat views → bundle.js
npm start       # http://127.0.0.1:4318
```

ou dev mode (watch + restart):

```bash
npm run dev
```

### 6. Testes

```bash
npm test
```

---

## Arquitetura

```
maffini-dashboard/
├── server/
│   ├── index.js          # http nativo + route registry
│   ├── lib/
│   │   ├── config.js     # .env + maffini.config.json
│   │   ├── router.js     # send/sendError/readJson
│   │   ├── auth.js       # basic auth + scrypt + rate limit
│   │   ├── legalops.js   # spawn legalops Python CLI
│   │   └── store.js      # JSON file store (atomic)
│   └── routes/           # health, prazos, intimacao, contract, dsar, audit, clients
├── public/
│   ├── index.html
│   ├── css/{brand,views}.css
│   ├── views/*.js        # vanilla, concat para bundle.js
│   ├── bundle.js         # gerado por scripts/build.js
│   └── manifest.json
├── scripts/{build,dev}.js
├── data/                 # gitignored — JSON stores + audit.db
└── test/                 # node --test
```

## API

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/brand` | GET | brand + áreas (público) |
| `/api/health` | GET | LegalOps health passthrough |
| `/api/prazos` | GET/POST | lista/cria prazo |
| `/api/prazos/:id` | PATCH/DELETE | atualiza/remove |
| `/api/intimacao/process` | POST | pipeline LegalOps (redact + parse + calc + audit) |
| `/api/intimacao/redact` | POST | só redaction |
| `/api/contract/analyze` | POST | risco contratual |
| `/api/dsar/process` | POST | DSAR LGPD Art. 18/19 |
| `/api/dsar` | GET | lista DSARs |
| `/api/audit/verify` | GET | integridade hash chain |
| `/api/audit/list` | GET | entradas |
| `/api/clients` | GET/POST | mini CRM (aliases) |
| `/api/clients/:id` | PATCH/DELETE | atualiza/remove |

Auth: HTTP Basic auth em todas as rotas exceto `/api/brand`.

## Segurança / LGPD

- **NUNCA PII real em logs** — pipeline LegalOps redige antes de qualquer persist.
- **Hash chain audit** com HMAC-SHA256 opcional (`LEGALOPS_AUDIT_HMAC_KEY`) — tamper-evidence.
- **Basic auth + scrypt** + rate limit 10 fails/15min/IP.
- **Body cap** 1MB padrão por request (5MB para uploads de texto).
- **subprocess sem shell** — args sempre array.
- **same-origin** por default; `MAFFINI_CORS` opt-in.
- Senha NUNCA logada · `.env` mode 600 · stores JSON mode 600.

## Deploy

systemd unit example:

```ini
[Unit]
Description=Maffini Dashboard
After=network.target

[Service]
Type=simple
User=maffini
WorkingDirectory=/opt/maffini-dashboard
EnvironmentFile=/opt/maffini-dashboard/.env
ExecStart=/usr/bin/node server/index.js
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Reverse proxy (Caddy) com HTTPS:

```
maffini.local {
  reverse_proxy 127.0.0.1:4318
  encode gzip
}
```

## Roadmap

- [x] v0.1 — scaffold + home/prazos/intimações/audit/dsar/contratos/clientes/config
- [x] v0.2 — templates .docx (bridge `doc-template`) · notificações WA/email/Slack (bridge `notify`) · PWA offline (sw.js) · calendário .ics (export route)
- [ ] v0.3 — piloto Tia May: deploy + logo real + paleta confirmada + training
- [ ] v1.0 — M365 ingest automático · WhatsApp prod · backup off-site

## License

Privado · uso interno Maffini & Rangel.
