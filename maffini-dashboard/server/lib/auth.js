'use strict';
// Basic auth single-user — Maffini Dashboard.
//
// Aceita 2 modos:
//  1. MAFFINI_AUTH_PASS_HASH = "scrypt$<salt-hex>$<hash-hex>"  (prod)
//  2. MAFFINI_AUTH_PASS = plaintext                            (dev only)
//
// Em prod NUNCA usar plaintext.
//
// Rate limit em memória: 10 fails/15min/IP → 401 mesmo com senha certa.

const crypto = require('crypto');

const SCRYPT_N = 16384;
const SCRYPT_R = 8;
const SCRYPT_P = 1;
const HASH_LEN = 32;

const failCache = new Map(); // ip → { count, firstAt }
const FAIL_WINDOW_MS = 15 * 60 * 1000;
const FAIL_THRESHOLD = 10;

function hashPassword(password, salt = crypto.randomBytes(16)) {
  const hash = crypto.scryptSync(password, salt, HASH_LEN, {
    N: SCRYPT_N, r: SCRYPT_R, p: SCRYPT_P
  });
  return `scrypt$${salt.toString('hex')}$${hash.toString('hex')}`;
}

function verifyPassword(password, stored) {
  if (!stored) return false;
  if (!stored.startsWith('scrypt$')) {
    // Dev-only plaintext mode.
    return crypto.timingSafeEqual(
      Buffer.from(password.padEnd(64, '\0')),
      Buffer.from(stored.padEnd(64, '\0'))
    );
  }
  const [, saltHex, expectedHex] = stored.split('$');
  if (!saltHex || !expectedHex) return false;
  const salt = Buffer.from(saltHex, 'hex');
  const expected = Buffer.from(expectedHex, 'hex');
  const actual = crypto.scryptSync(password, salt, HASH_LEN, {
    N: SCRYPT_N, r: SCRYPT_R, p: SCRYPT_P
  });
  return crypto.timingSafeEqual(expected, actual);
}

function rateLimitCheck(ip) {
  const now = Date.now();
  const rec = failCache.get(ip);
  if (!rec) return true;
  if (now - rec.firstAt > FAIL_WINDOW_MS) {
    failCache.delete(ip);
    return true;
  }
  return rec.count < FAIL_THRESHOLD;
}

function rateLimitNote(ip) {
  const now = Date.now();
  const rec = failCache.get(ip);
  if (!rec || now - rec.firstAt > FAIL_WINDOW_MS) {
    failCache.set(ip, { count: 1, firstAt: now });
    return;
  }
  rec.count += 1;
}

function rateLimitReset(ip) { failCache.delete(ip); }

// Login auth is OPTIONAL (single-user mode). It is "enabled" only when
// MAFFINI_AUTH_USER is set to a non-empty value. When disabled, the basic-auth
// wall is skipped entirely — but the boot guard (assertAuthHostSafe) ensures the
// server is loopback-bound so an auth-less dashboard is never exposed on a LAN/WAN.
function authEnabled() {
  return !!(process.env.MAFFINI_AUTH_USER && process.env.MAFFINI_AUTH_USER.trim());
}

const LOOPBACK_HOSTS = new Set(['127.0.0.1', '::1', 'localhost', '0:0:0:0:0:0:0:1']);

function isLoopbackHost(host) {
  if (!host) return false;
  let h = String(host).trim().toLowerCase();
  // strip ipv6 brackets and zone id
  if (h.startsWith('[') && h.endsWith(']')) h = h.slice(1, -1);
  h = h.split('%')[0];
  if (LOOPBACK_HOSTS.has(h)) return true;
  // entire 127.0.0.0/8 range is loopback
  if (/^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(h)) return true;
  return false;
}

// Boot guard: when login auth is DISABLED, the server MUST be loopback-bound.
// Throws on a non-loopback host so an auth-less dashboard never listens on a
// LAN/WAN interface. No-op when auth is enabled. Returns the chosen mode.
function assertAuthHostSafe(host) {
  if (authEnabled()) return 'basic';
  if (!isLoopbackHost(host)) {
    throw new Error(
      `Refusing to start: login auth is disabled (MAFFINI_AUTH_USER unset) but ` +
      `host "${host}" is not loopback. Either bind to 127.0.0.1/::1/localhost, ` +
      `or set MAFFINI_AUTH_USER + MAFFINI_AUTH_PASS to enable basic auth.`
    );
  }
  return 'disabled';
}

function parseBasicAuth(header) {
  if (!header || !header.toLowerCase().startsWith('basic ')) return null;
  const decoded = Buffer.from(header.slice(6).trim(), 'base64').toString('utf8');
  const idx = decoded.indexOf(':');
  if (idx < 0) return null;
  return { user: decoded.slice(0, idx), pass: decoded.slice(idx + 1) };
}

// Middleware-style: returns true if authorized; otherwise writes 401 + returns false.
function authorize(req, res, { realm = 'Maffini Dashboard', publicPaths = [] } = {}) {
  const url = req.url || '';
  if (publicPaths.some(p => url === p || url.startsWith(p + '?'))) return true;

  // Login auth disabled (single-user loopback mode) → no basic-auth wall.
  // Safe because the boot guard refuses to start on a non-loopback host here.
  // NOTE: this only bypasses LOGIN auth — the per-command approval gate in
  // routes/command.js is independent and stays enforced regardless.
  if (!authEnabled()) return true;

  const ip = (req.socket && req.socket.remoteAddress) || 'unknown';
  if (!rateLimitCheck(ip)) {
    res.writeHead(429, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'too many failed attempts; try later' }));
    return false;
  }

  const expectedUser = process.env.MAFFINI_AUTH_USER;
  const storedPass = process.env.MAFFINI_AUTH_PASS_HASH || process.env.MAFFINI_AUTH_PASS;
  if (!expectedUser || !storedPass) {
    res.writeHead(503, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'auth not configured; set MAFFINI_AUTH_USER + MAFFINI_AUTH_PASS' }));
    return false;
  }

  const creds = parseBasicAuth(req.headers['authorization']);
  if (!creds || creds.user !== expectedUser || !verifyPassword(creds.pass, storedPass)) {
    rateLimitNote(ip);
    res.writeHead(401, {
      'WWW-Authenticate': `Basic realm="${realm}", charset="UTF-8"`,
      'Content-Type': 'application/json'
    });
    res.end(JSON.stringify({ error: 'unauthorized' }));
    return false;
  }

  rateLimitReset(ip);
  return true;
}

module.exports = {
  authorize, hashPassword, verifyPassword, parseBasicAuth,
  authEnabled, isLoopbackHost, assertAuthHostSafe,
  // exposed for tests
  rateLimitCheck, rateLimitNote, rateLimitReset
};
