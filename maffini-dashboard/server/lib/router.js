'use strict';
// Minimal router helpers — JSON response + body parsing.

function send(res, status, body, headers = {}) {
  const isJson = typeof body === 'object' && body !== null && !Buffer.isBuffer(body);
  const payload = isJson ? JSON.stringify(body) : body;
  const baseHeaders = isJson
    ? { 'Content-Type': 'application/json; charset=utf-8' }
    : {};
  res.writeHead(status, Object.assign(baseHeaders, headers));
  if (payload) res.end(payload);
  else res.end();
}

function sendError(res, status, message, extra = {}) {
  send(res, status, Object.assign({ error: message }, extra));
}

function readBody(req, { maxBytes = 1_048_576 } = {}) {
  return new Promise((resolve, reject) => {
    let total = 0;
    const chunks = [];
    req.on('data', chunk => {
      total += chunk.length;
      if (total > maxBytes) {
        req.destroy();
        return reject(new Error(`body exceeds ${maxBytes} bytes`));
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

async function readJson(req, opts) {
  const raw = await readBody(req, opts);
  if (!raw) return {};
  try { return JSON.parse(raw); }
  catch (e) { throw new Error(`invalid JSON body: ${e.message}`); }
}

module.exports = { send, sendError, readBody, readJson };
