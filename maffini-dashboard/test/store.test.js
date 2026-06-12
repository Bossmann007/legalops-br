'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { JSONStore, readJSON, writeJSON } = require('../server/lib/store');

function tmpFile() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'maf-store-'));
  return path.join(dir, 'data.json');
}

test('writeJSON / readJSON roundtrip', () => {
  const f = tmpFile();
  writeJSON(f, { a: 1 });
  assert.deepEqual(readJSON(f, null), { a: 1 });
});

test('writeJSON sets mode 0600', () => {
  const f = tmpFile();
  writeJSON(f, { x: 1 });
  const mode = fs.statSync(f).mode & 0o777;
  assert.equal(mode, 0o600);
});

test('readJSON returns fallback on missing/corrupt', () => {
  assert.deepEqual(readJSON('/no/such/file', { fb: true }), { fb: true });
});

test('JSONStore create/get/update/remove', () => {
  const store = new JSONStore(tmpFile());
  const a = store.create({ alias: 'CLI-001' });
  assert.ok(a.id);
  assert.equal(a.alias, 'CLI-001');
  assert.ok(a.createdAt);

  const got = store.get(a.id);
  assert.equal(got.alias, 'CLI-001');

  const upd = store.update(a.id, { alias: 'CLI-001-v2' });
  assert.equal(upd.alias, 'CLI-001-v2');
  assert.ok(upd.updatedAt);

  assert.equal(store.list().length, 1);
  assert.equal(store.remove(a.id), true);
  assert.equal(store.list().length, 0);
});

test('JSONStore returns null for missing get/update', () => {
  const store = new JSONStore(tmpFile());
  assert.equal(store.get('nope'), null);
  assert.equal(store.update('nope', {}), null);
  assert.equal(store.remove('nope'), false);
});
