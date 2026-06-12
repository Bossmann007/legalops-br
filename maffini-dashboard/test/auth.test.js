'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {
  hashPassword, verifyPassword, parseBasicAuth, authorize,
  rateLimitCheck, rateLimitNote, rateLimitReset
} = require('../server/lib/auth');

function mockRes() {
  const r = { headers: null, status: null, body: '' };
  r.writeHead = (s, h) => { r.status = s; r.headers = h; };
  r.end = (b) => { r.body = b || ''; };
  return r;
}
function mockReq(authHeader, ip = '1.2.3.4', url = '/api/x') {
  return {
    url,
    headers: authHeader ? { 'authorization': authHeader } : {},
    socket: { remoteAddress: ip }
  };
}

test('hashPassword/verifyPassword roundtrip', () => {
  const hash = hashPassword('hunter2');
  assert.ok(hash.startsWith('scrypt$'));
  assert.equal(verifyPassword('hunter2', hash), true);
  assert.equal(verifyPassword('wrong', hash), false);
});

test('verifyPassword plaintext dev fallback', () => {
  assert.equal(verifyPassword('abc', 'abc'), true);
  assert.equal(verifyPassword('abc', 'xyz'), false);
});

test('parseBasicAuth decodes user:pass', () => {
  const enc = 'Basic ' + Buffer.from('maylin:secret').toString('base64');
  const r = parseBasicAuth(enc);
  assert.deepEqual(r, { user: 'maylin', pass: 'secret' });
});

test('parseBasicAuth returns null for malformed', () => {
  assert.equal(parseBasicAuth(null), null);
  assert.equal(parseBasicAuth('Bearer xyz'), null);
  assert.equal(parseBasicAuth('Basic ' + Buffer.from('no-colon').toString('base64')), null);
});

test('authorize passes through when login auth disabled (no AUTH_USER)', () => {
  // Login auth is OPTIONAL: with MAFFINI_AUTH_USER unset, the basic-auth wall
  // is skipped (single-user loopback mode). The boot guard enforces loopback.
  const u = process.env.MAFFINI_AUTH_USER;
  const p = process.env.MAFFINI_AUTH_PASS;
  delete process.env.MAFFINI_AUTH_USER;
  delete process.env.MAFFINI_AUTH_PASS;
  delete process.env.MAFFINI_AUTH_PASS_HASH;
  const req = mockReq();
  const res = mockRes();
  const ok = authorize(req, res);
  assert.equal(ok, true);
  assert.equal(res.status, null);
  if (u) process.env.MAFFINI_AUTH_USER = u;
  if (p) process.env.MAFFINI_AUTH_PASS = p;
});

test('authorize succeeds with correct credentials', () => {
  process.env.MAFFINI_AUTH_USER = 'maylin';
  process.env.MAFFINI_AUTH_PASS = 'secret';
  rateLimitReset('1.2.3.4');
  const cred = 'Basic ' + Buffer.from('maylin:secret').toString('base64');
  const req = mockReq(cred);
  const res = mockRes();
  const ok = authorize(req, res);
  assert.equal(ok, true);
  delete process.env.MAFFINI_AUTH_USER;
  delete process.env.MAFFINI_AUTH_PASS;
});

test('authorize 401 + WWW-Authenticate on wrong password', () => {
  process.env.MAFFINI_AUTH_USER = 'maylin';
  process.env.MAFFINI_AUTH_PASS = 'secret';
  rateLimitReset('1.2.3.5');
  const cred = 'Basic ' + Buffer.from('maylin:wrong').toString('base64');
  const req = mockReq(cred, '1.2.3.5');
  const res = mockRes();
  const ok = authorize(req, res);
  assert.equal(ok, false);
  assert.equal(res.status, 401);
  assert.ok(res.headers['WWW-Authenticate'].includes('Basic'));
  delete process.env.MAFFINI_AUTH_USER;
  delete process.env.MAFFINI_AUTH_PASS;
});

test('authorize lets public paths through without creds', () => {
  delete process.env.MAFFINI_AUTH_USER;
  const req = mockReq(null, '1.2.3.6', '/api/brand');
  const res = mockRes();
  const ok = authorize(req, res, { publicPaths: ['/api/brand'] });
  assert.equal(ok, true);
});

test('rate limit blocks after threshold', () => {
  const ip = '9.9.9.9';
  rateLimitReset(ip);
  for (let i = 0; i < 10; i++) rateLimitNote(ip);
  assert.equal(rateLimitCheck(ip), false);
  rateLimitReset(ip);
  assert.equal(rateLimitCheck(ip), true);
});
