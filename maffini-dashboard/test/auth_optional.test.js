'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {
  authorize, authEnabled, isLoopbackHost, assertAuthHostSafe
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

function withoutAuthUser(fn) {
  const u = process.env.MAFFINI_AUTH_USER;
  delete process.env.MAFFINI_AUTH_USER;
  try { fn(); } finally { if (u !== undefined) process.env.MAFFINI_AUTH_USER = u; }
}

test('authEnabled false when MAFFINI_AUTH_USER unset/empty', () => {
  withoutAuthUser(() => {
    assert.equal(authEnabled(), false);
    process.env.MAFFINI_AUTH_USER = '   ';
    assert.equal(authEnabled(), false);
    process.env.MAFFINI_AUTH_USER = 'maylin';
    assert.equal(authEnabled(), true);
  });
});

test('auth-disabled mode lets a request through without creds', () => {
  withoutAuthUser(() => {
    const req = mockReq(null, '1.2.3.4', '/api/command/run');
    const res = mockRes();
    const ok = authorize(req, res);
    assert.equal(ok, true);
    assert.equal(res.status, null); // no 401/503 written
  });
});

test('isLoopbackHost recognizes loopback addresses', () => {
  for (const h of ['127.0.0.1', '::1', 'localhost', '[::1]', '127.5.5.5', 'LOCALHOST']) {
    assert.equal(isLoopbackHost(h), true, `${h} should be loopback`);
  }
  for (const h of ['0.0.0.0', '192.168.0.10', 'example.com', '', null]) {
    assert.equal(isLoopbackHost(h), false, `${h} should not be loopback`);
  }
});

test('boot guard rejects auth-disabled + non-loopback host', () => {
  withoutAuthUser(() => {
    assert.throws(() => assertAuthHostSafe('0.0.0.0'), /Refusing to start/);
    assert.throws(() => assertAuthHostSafe('192.168.1.5'), /Refusing to start/);
  });
});

test('boot guard allows auth-disabled + loopback host', () => {
  withoutAuthUser(() => {
    assert.equal(assertAuthHostSafe('127.0.0.1'), 'disabled');
    assert.equal(assertAuthHostSafe('localhost'), 'disabled');
  });
});

test('boot guard allows non-loopback host when auth enabled', () => {
  const u = process.env.MAFFINI_AUTH_USER;
  process.env.MAFFINI_AUTH_USER = 'maylin';
  try {
    assert.equal(assertAuthHostSafe('0.0.0.0'), 'basic');
  } finally {
    if (u === undefined) delete process.env.MAFFINI_AUTH_USER;
    else process.env.MAFFINI_AUTH_USER = u;
  }
});
