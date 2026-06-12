'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const { parseEnv, defaults, bust, load } = require('../server/lib/config');

test('parseEnv ignores comments and blank lines', () => {
  const out = parseEnv('# comment\n\nFOO=bar\nBAR=baz\n');
  assert.equal(out.FOO, 'bar');
  assert.equal(out.BAR, 'baz');
  assert.ok(!('# comment' in out));
});

test('parseEnv strips matching quotes', () => {
  const out = parseEnv('A="hello"\nB=\'world\'\nC="multi word"\n');
  assert.equal(out.A, 'hello');
  assert.equal(out.B, 'world');
  assert.equal(out.C, 'multi word');
});

test('parseEnv tolerates missing equals and lone keys', () => {
  const out = parseEnv('JUST_A_KEY\n=onlyvalue\n');
  assert.deepEqual(Object.keys(out), []);
});

test('defaults shape is stable', () => {
  const d = defaults();
  assert.equal(d.server.port, 4318);
  assert.equal(d.prazoThresholds.urgentDays, 3);
  assert.equal(d.prazoThresholds.warningDays, 7);
  assert.ok(Array.isArray(d.areas));
});

test('load() picks up MAFFINI_PORT env override', () => {
  const original = process.env.MAFFINI_PORT;
  process.env.MAFFINI_PORT = '9999';
  bust();
  const cfg = load();
  assert.equal(cfg.server.port, 9999);
  if (original === undefined) delete process.env.MAFFINI_PORT;
  else process.env.MAFFINI_PORT = original;
  bust();
});

test('load() resolves relative paths to repo root', () => {
  bust();
  const cfg = load();
  assert.ok(path.isAbsolute(cfg.paths.prazosStore));
  assert.ok(cfg.paths.prazosStore.includes('data'));
});

test('load() resolves tilde to homedir', () => {
  // Use a tmp config to avoid stomping the real one
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'maf-cfg-'));
  process.env.LEGALOPS_AUDIT_DB = '~/audit.db';
  bust();
  const cfg = load();
  assert.equal(cfg.paths.auditDb, path.join(os.homedir(), 'audit.db'));
  delete process.env.LEGALOPS_AUDIT_DB;
  bust();
  fs.rmSync(tmp, { recursive: true, force: true });
});
