'use strict';
// Config loader — copy of agentic-os pattern.
// Loads `.env` (minimal parser, no deps) + `maffini.config.json` defaults.
// Secrets NEVER live in maffini.config.json — they come from .env.

const fs = require('fs');
const path = require('path');
const os = require('os');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const CONFIG_PATH = path.join(REPO_ROOT, 'maffini.config.json');
const ENV_PATH = path.join(REPO_ROOT, '.env');

let _cache = null;

function parseEnv(text) {
  const out = {};
  for (const raw of String(text).split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq < 1) continue;
    const key = line.slice(0, eq).trim();
    let val = line.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) ||
        (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }
  return out;
}

function loadEnv() {
  let text = '';
  try { text = fs.readFileSync(ENV_PATH, 'utf8'); }
  catch { return; }
  const parsed = parseEnv(text);
  for (const [k, v] of Object.entries(parsed)) {
    if (process.env[k] === undefined) process.env[k] = v;
  }
}

function defaults() {
  return {
    brand: {
      name: 'Maffini Dashboard',
      full: 'Maffini & Rangel — Centro de Comando',
      tagline: 'Soluções mais ágeis e menos onerosas',
      owner: 'Dra. Maylin'
    },
    areas: [],
    prazoThresholds: { urgentDays: 3, warningDays: 7 },
    server: { port: 4318, host: '127.0.0.1' },
    paths: {
      legalopsBin: '',
      auditDb: 'data/audit.db',
      clientsStore: 'data/clients.json',
      prazosStore: 'data/prazos.json',
      settingsStore: 'data/settings.json'
    },
    notification: { channels: [], minPrazoDays: 3 }
  };
}

function applyEnvOverrides(cfg) {
  if (process.env.MAFFINI_PORT) cfg.server.port = parseInt(process.env.MAFFINI_PORT, 10);
  if (process.env.MAFFINI_HOST) cfg.server.host = process.env.MAFFINI_HOST;
  if (process.env.LEGALOPS_BIN) cfg.paths.legalopsBin = process.env.LEGALOPS_BIN;
  if (process.env.LEGALOPS_AUDIT_DB) cfg.paths.auditDb = process.env.LEGALOPS_AUDIT_DB;
  return cfg;
}

function resolvePaths(cfg) {
  for (const key of Object.keys(cfg.paths)) {
    const v = cfg.paths[key];
    if (!v) continue;
    if (v.startsWith('~')) cfg.paths[key] = v.replace('~', os.homedir());
    else if (!path.isAbsolute(v)) cfg.paths[key] = path.join(REPO_ROOT, v);
  }
  return cfg;
}

function load() {
  if (_cache) return _cache;
  loadEnv();
  let onDisk = {};
  try { onDisk = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8')); }
  catch { /* defaults only */ }
  let cfg = Object.assign({}, defaults(), onDisk);
  cfg = applyEnvOverrides(cfg);
  cfg = resolvePaths(cfg);
  _cache = cfg;
  return _cache;
}

function bust() { _cache = null; }

module.exports = { load, defaults, bust, parseEnv, REPO_ROOT, ENV_PATH, CONFIG_PATH };
