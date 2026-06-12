'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const commandRoutes = require('../server/routes/command');

// ── Test harness ────────────────────────────────────────────────────
// Build an isolated cfg pointing data stores at a tmp dir so approvals.json
// and prazos.json never touch the real data/ dir.
function makeCfg() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'maf-cmd-'));
  return {
    dir,
    paths: {
      prazosStore: path.join(dir, 'prazos.json'),
      auditDb: path.join(dir, 'audit.db')
    }
  };
}

// Minimal req: emits the JSON body then ends.
function mockReq(body) {
  const raw = Buffer.from(JSON.stringify(body));
  const handlers = {};
  const req = {
    on(ev, fn) { handlers[ev] = fn; return req; },
    destroy() {}
  };
  process.nextTick(() => {
    if (handlers.data) handlers.data(raw);
    if (handlers.end) handlers.end();
  });
  return req;
}

// Minimal res capturing status + parsed JSON body.
function mockRes() {
  return {
    statusCode: null,
    body: null,
    writeHead(status) { this.statusCode = status; return this; },
    end(payload) { this.body = payload ? JSON.parse(payload) : null; }
  };
}

async function run(routes, key, body) {
  const res = mockRes();
  await routes[key](mockReq(body), res, {});
  return res;
}

test('command/list returns groups + commands', async () => {
  const routes = commandRoutes(makeCfg());
  const res = await run(routes, 'GET /api/command/list', {});
  assert.equal(res.statusCode, 200);
  assert.ok(Array.isArray(res.body.groups));
  assert.ok(Array.isArray(res.body.commands));
  assert.ok(res.body.commands.find(c => c.id === 'intimacao_pipeline'));
});

test('run without approved:true on approval-required command → 403', async () => {
  const routes = commandRoutes(makeCfg());
  const res = await run(routes, 'POST /api/command/run', {
    id: 'red_flags_scan', inputs: { text: 'x' }
  });
  assert.equal(res.statusCode, 403);
  assert.match(res.body.error, /approval required/);
});

test('run with missing required input → 400', async () => {
  const routes = commandRoutes(makeCfg());
  const res = await run(routes, 'POST /api/command/run', {
    id: 'red_flags_scan', inputs: {}, approved: true
  });
  assert.equal(res.statusCode, 400);
  assert.match(res.body.error, /missing required input: text/);
});

test('internal command → 501 not_implemented', async () => {
  // bacen_cvm_check stays internal/deferred (network feed — no CLI bridge).
  const routes = commandRoutes(makeCfg());
  const res = await run(routes, 'POST /api/command/run', {
    id: 'bacen_cvm_check', inputs: {}, approved: true
  });
  assert.equal(res.statusCode, 501);
  assert.equal(res.body.status, 'not_implemented');
  assert.equal(res.body.module, 'bacen_cvm_feeds');
});

test('claude_legal command → 501 not_implemented when ANTHROPIC_API_KEY unset', async () => {
  const prev = process.env.ANTHROPIC_API_KEY;
  delete process.env.ANTHROPIC_API_KEY;
  try {
    const routes = commandRoutes(makeCfg());
    const res = await run(routes, 'POST /api/command/run', {
      id: 'cfl_triage_nda', inputs: { text: 'nda body' }, approved: true
    });
    assert.equal(res.statusCode, 501);
    assert.equal(res.body.status, 'not_implemented');
    assert.equal(res.body.skill, 'triage-nda');
    assert.match(res.body.note, /ANTHROPIC_API_KEY/);
  } finally {
    if (prev !== undefined) process.env.ANTHROPIC_API_KEY = prev;
  }
});

test('unknown command → 404', async () => {
  const routes = commandRoutes(makeCfg());
  const res = await run(routes, 'POST /api/command/run', {
    id: 'no_such_cmd', approved: true
  });
  assert.equal(res.statusCode, 404);
});

test('approval record written without raw redactable PII', async () => {
  const cfg = makeCfg();
  const routes = commandRoutes(cfg);
  const secret = 'JOAO DA SILVA CPF 123.456.789-00';
  // m365_fetch stays internal/deferred and exercises the approval-record path
  // without invoking the legalops binary. Its `descricao`-less inputs include no
  // redactable PII field, so we craft one via a redactable-less input still hashed.
  const res = await run(routes, 'POST /api/command/run', {
    id: 'm365_fetch', inputs: { days: 7, sender_filter: secret }, approved: true
  });
  assert.equal(res.statusCode, 501); // attempted run still records approval

  const file = path.join(cfg.dir, 'approvals.json');
  const stored = fs.readFileSync(file, 'utf8');
  // The non-redactable inputs are hashed (not stored raw) — only inputs_hash persists.
  assert.ok(!stored.includes(secret), 'raw input leaked into store');
  assert.ok(!stored.includes('123.456.789-00'), 'raw CPF leaked');

  const parsed = JSON.parse(stored);
  const rec = parsed.items[0];
  assert.equal(rec.command_id, 'm365_fetch');
  assert.match(rec.inputs_hash, /^[0-9a-f]{64}$/);
});
