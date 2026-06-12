# Maffini Dashboard — Project Config

## Stack
- Node.js 20+ · http nativo · vanilla JS · CSS variables
- Zero runtime deps · tests via `node --test`
- Bridge: subprocess `legalops` (Python CLI · LegalOps BR)

## Commands

```bash
npm run build   # concat public/views/*.js → public/bundle.js
npm start       # boot server :4318
npm run dev     # watch + restart
npm test        # node --test
```

## Architecture

```
server/{index.js, lib/, routes/}
public/{index.html, css/, views/, bundle.js, manifest.json, img/}
scripts/{build.js, dev.js}
data/         (gitignored — JSON stores + audit.db)
test/         (node --test)
```

### Padrões
- **Route registry**: cada arquivo `server/routes/X.js` exporta `(cfg) => { 'METHOD /api/path': handler, ... }`
- **Views**: cada `public/views/X.js` chama `MAF.register(name, async () => domNode)`
- **Build**: concat puro (sem esbuild) — replica lesson agentic-os Wave v5
- **`.env`**: loader minimal sem dep · secrets nunca em `maffini.config.json`
- **XSS-safe**: NUNCA `innerHTML` com dado externo · usar `MAF.el()` + `textContent`

## Rules

- Type hints opcionais (JS); JSDoc preferido em libs reusáveis
- Zero runtime deps — qualquer dep nova requer PR review
- NUNCA `shell=true` em subprocess; args sempre array
- Body limits: 1MB padrão · 5MB pra textos longos
- Auth: scrypt hash em prod (`MAFFINI_AUTH_PASS_HASH`); plaintext só dev
- Rate limit: 10 fails/15min/IP

## LGPD

- PII real **NUNCA** em logs · banco · `.env` · git history
- Sempre pseudonimizar via `legalops` antes de persistir
- Audit chain via LegalOps `oab_sigilo` (HMAC opcional)
- Clientes: aliases only (`CLI-021`, hash:abc) — nunca nome real
- Backup audit.db: retenção 5 anos (Art. 37)

## Tests

- `node --test` (sem framework dep)
- Cobertura mínima: config + auth + router + store + legalops bridge
- Subprocess `legalops` mockado (não roda Python real em CI)

## Status

v0.1 · scaffold MVP · 7 views (home, prazos, intimacoes, contratos, dsar, audit, clientes, config)
Próximo: testes integration + git push GitHub privado + piloto Tia May

## Threads abertas

- [ ] v0.2: templates engine .docx · notificações canais · PWA sw
- [ ] Confirmar paleta com Tia May (navy+gold proposto)
- [ ] Logo SVG real do escritório (atualmente placeholder M&R)
- [ ] Deploy systemd em máquina Tia May ou VPS BR
