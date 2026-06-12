'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { runLegalops, LegalOpsError, buildEnv, MAX_OUT_BYTES } = require('../server/lib/legalops');

test('refuses to run without LEGALOPS_PII_SALT', async () => {
  const original = process.env.LEGALOPS_PII_SALT;
  delete process.env.LEGALOPS_PII_SALT;
  await assert.rejects(() => runLegalops(['health']), /LEGALOPS_PII_SALT/);
  if (original) process.env.LEGALOPS_PII_SALT = original;
});

test('rejects non-array args', async () => {
  await assert.rejects(() => runLegalops('health'), /array/);
});

test('buildEnv copies LEGALOPS_PII_SALT but not unrelated vars', () => {
  process.env.LEGALOPS_PII_SALT = 'test-salt-32-bytes-syntheticxxxx';
  process.env.SOME_UNRELATED_SECRET = 'should-not-pass';
  const env = buildEnv();
  assert.equal(env.LEGALOPS_PII_SALT, 'test-salt-32-bytes-syntheticxxxx');
  assert.ok(!('SOME_UNRELATED_SECRET' in env));
  assert.ok(env.PATH);
  assert.ok(env.LANG);
  delete process.env.SOME_UNRELATED_SECRET;
});

test('LegalOpsError carries code + stderr metadata', () => {
  const e = new LegalOpsError('oops', { code: 2, stderr: 'err msg' });
  assert.equal(e.message, 'oops');
  assert.equal(e.code, 2);
  assert.equal(e.stderr, 'err msg');
  assert.equal(e.name, 'LegalOpsError');
});

test('MAX_OUT_BYTES is sane', () => {
  assert.equal(MAX_OUT_BYTES, 5 * 1024 * 1024);
});

test('rejects when bin not found', async () => {
  process.env.LEGALOPS_PII_SALT = 'test-salt-32-bytes-syntheticxxxx';
  await assert.rejects(
    () => runLegalops(['health'], { bin: '/no/such/binary/path/legalops-fake' }),
    /spawn failed/
  );
});
