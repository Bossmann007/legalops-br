'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { send, sendError, readBody, readJson } = require('../server/lib/router');
const { Readable } = require('node:stream');

function mockRes() {
  const r = { status: 0, headers: null, body: null };
  r.writeHead = (s, h) => { r.status = s; r.headers = h; };
  r.end = (b) => { r.body = b || ''; };
  return r;
}
function mockReq(payload) {
  const r = new Readable({ read() {} });
  r.push(payload);
  r.push(null);
  return r;
}

test('send writes JSON when body is object', () => {
  const res = mockRes();
  send(res, 200, { ok: true });
  assert.equal(res.status, 200);
  assert.equal(res.headers['Content-Type'], 'application/json; charset=utf-8');
  assert.deepEqual(JSON.parse(res.body), { ok: true });
});

test('sendError yields {error: msg}', () => {
  const res = mockRes();
  sendError(res, 400, 'bad');
  assert.equal(res.status, 400);
  assert.deepEqual(JSON.parse(res.body), { error: 'bad' });
});

test('readBody collects stream chunks', async () => {
  const req = mockReq('hello world');
  const out = await readBody(req);
  assert.equal(out, 'hello world');
});

test('readBody enforces maxBytes', async () => {
  const req = mockReq('x'.repeat(100));
  await assert.rejects(() => readBody(req, { maxBytes: 10 }));
});

test('readJson parses JSON body', async () => {
  const req = mockReq(JSON.stringify({ a: 1 }));
  const out = await readJson(req);
  assert.deepEqual(out, { a: 1 });
});

test('readJson returns empty object for empty body', async () => {
  const req = mockReq('');
  const out = await readJson(req);
  assert.deepEqual(out, {});
});

test('readJson rejects malformed JSON', async () => {
  const req = mockReq('not-json{');
  await assert.rejects(() => readJson(req), /invalid JSON/);
});
