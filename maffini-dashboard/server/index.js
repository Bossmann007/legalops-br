'use strict';
// Maffini Dashboard — HTTP server entry.
//
// Padrão arquitetural copy de agentic-os:
//   - http nativo + roteador de pattern matching simples
//   - cada arquivo em routes/ exporta map "METHOD /path": handler(req,res,params)
//   - lib/config carrega .env + maffini.config.json
//
// Segurança: basic auth obrigatório em /api/* (exceto /api/health opcional).

const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const cfg = require('./lib/config').load();
const { send, sendError } = require('./lib/router');
const { authorize } = require('./lib/auth');

const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const PORT = cfg.server.port;
const HOST = cfg.server.host;
const PUBLIC_API_PATHS = ['/api/brand', '/api/command/list']; // OK público pra carregar shell

// Registry: { 'GET /api/x': fn, 'POST /api/y/:id': fn }
const routes = Object.assign({},
  require('./routes/health')(cfg),
  require('./routes/prazos')(cfg),
  require('./routes/intimacao')(cfg),
  require('./routes/contract')(cfg),
  require('./routes/dsar')(cfg),
  require('./routes/audit')(cfg),
  require('./routes/clients')(cfg),
  require('./routes/command')(cfg)
);

// Pattern matcher — extrai :params em URL.
function matchRoute(method, pathname) {
  const direct = `${method} ${pathname}`;
  if (routes[direct]) return { handler: routes[direct], params: {} };

  for (const key of Object.keys(routes)) {
    const [m, pattern] = key.split(' ');
    if (m !== method) continue;
    if (!pattern.includes(':')) continue;
    const re = new RegExp('^' + pattern.replace(/:(\w+)/g, '(?<$1>[^/]+)') + '$');
    const match = pathname.match(re);
    if (match) return { handler: routes[key], params: match.groups || {} };
  }
  return null;
}

const STATIC_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.woff2': 'font/woff2',
  '.ico':  'image/x-icon',
  '.webmanifest': 'application/manifest+json'
};

function safeJoin(root, requested) {
  const resolved = path.resolve(root, '.' + requested);
  if (!resolved.startsWith(root + path.sep) && resolved !== root) return null;
  return resolved;
}

function serveStatic(req, res, pathname) {
  let rel = pathname === '/' ? '/index.html' : pathname;
  const abs = safeJoin(PUBLIC_DIR, rel);
  if (!abs) return sendError(res, 403, 'forbidden');
  fs.stat(abs, (err, stat) => {
    if (err || !stat.isFile()) {
      // SPA fallback: serve index.html for unknown paths (no extension)
      if (!path.extname(pathname)) {
        return fs.readFile(path.join(PUBLIC_DIR, 'index.html'), (e2, buf) => {
          if (e2) return sendError(res, 404, 'not found');
          send(res, 200, buf, { 'Content-Type': 'text/html; charset=utf-8' });
        });
      }
      return sendError(res, 404, 'not found');
    }
    const ext = path.extname(abs).toLowerCase();
    const type = STATIC_TYPES[ext] || 'application/octet-stream';
    fs.readFile(abs, (e2, buf) => {
      if (e2) return sendError(res, 500, 'read error');
      const headers = { 'Content-Type': type };
      if (ext === '.woff2' || ext === '.png' || ext === '.svg') {
        headers['Cache-Control'] = 'public, max-age=86400';
      }
      send(res, 200, buf, headers);
    });
  });
}

const server = http.createServer(async (req, res) => {
  let parsed;
  try { parsed = new URL(req.url, `http://${req.headers.host || 'localhost'}`); }
  catch { return sendError(res, 400, 'bad request'); }
  const pathname = parsed.pathname;
  const method = req.method.toUpperCase();

  // CORS preflight (same-origin default → only allow if MAFFINI_CORS set)
  if (method === 'OPTIONS') {
    const origin = req.headers.origin || '';
    const allow = (process.env.MAFFINI_CORS || '').split(',').map(s => s.trim());
    if (allow.includes(origin)) {
      res.writeHead(204, {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      });
      return res.end();
    }
    return sendError(res, 403, 'origin not allowed');
  }

  // Static (UI)
  if (!pathname.startsWith('/api/')) {
    return serveStatic(req, res, pathname);
  }

  // API: auth gate
  if (!authorize(req, res, { publicPaths: PUBLIC_API_PATHS })) return;

  const match = matchRoute(method, pathname);
  if (!match) return sendError(res, 404, 'route not found');

  try {
    await match.handler(req, res, match.params);
  } catch (e) {
    sendError(res, 500, e.message);
  }
});

server.listen(PORT, HOST, () => {
  console.log(`Maffini Dashboard listening on http://${HOST}:${PORT}`);
});

module.exports = { server, routes, matchRoute };
