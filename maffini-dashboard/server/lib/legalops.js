'use strict';
// Bridge para o CLI `legalops` (Python). Roda subprocess, captura JSON, retorna.
//
// Segurança:
// - args SEMPRE array (sem shell=true)
// - timeout padrão 30s (kill SIGKILL após +5s grace)
// - max stdout 5MB (kill se exceder — evita DoS)
// - env mínimo + LEGALOPS_PII_SALT injetado de process.env
// - NUNCA loga stdin/stdout body — apenas tamanho e exit code

const { spawn } = require('child_process');

const DEFAULT_TIMEOUT_MS = 30_000;
const MAX_OUT_BYTES = 5 * 1024 * 1024;

class LegalOpsError extends Error {
  constructor(message, { code, stderr } = {}) {
    super(message);
    this.name = 'LegalOpsError';
    this.code = code;
    this.stderr = stderr;
  }
}

function buildEnv() {
  const env = {
    PATH: process.env.PATH,
    HOME: process.env.HOME,
    LANG: process.env.LANG || 'pt_BR.UTF-8',
    LC_ALL: process.env.LC_ALL || 'pt_BR.UTF-8'
  };
  if (process.env.LEGALOPS_PII_SALT) env.LEGALOPS_PII_SALT = process.env.LEGALOPS_PII_SALT;
  if (process.env.LEGALOPS_AUDIT_HMAC_KEY) env.LEGALOPS_AUDIT_HMAC_KEY = process.env.LEGALOPS_AUDIT_HMAC_KEY;
  if (process.env.LEGALOPS_SMTP_PASSWORD) env.LEGALOPS_SMTP_PASSWORD = process.env.LEGALOPS_SMTP_PASSWORD;
  return env;
}

/**
 * Roda `legalops <args>` com stdin opcional, retorna parsed JSON (ou raw string).
 *
 * @param {string[]} args  CLI args (sem shell — array literal)
 * @param {object}   opts  { stdin?: string, timeoutMs?: number, bin?: string }
 * @returns {Promise<object>}  parsed JSON ou { raw: string }
 */
function runLegalops(args, opts = {}) {
  const bin = opts.bin || process.env.LEGALOPS_BIN || 'legalops';
  const timeoutMs = opts.timeoutMs || DEFAULT_TIMEOUT_MS;
  if (!Array.isArray(args)) {
    return Promise.reject(new LegalOpsError('args must be an array'));
  }

  return new Promise((resolve, reject) => {
    const env = buildEnv();
    if (!env.LEGALOPS_PII_SALT) {
      return reject(new LegalOpsError(
        'LEGALOPS_PII_SALT not set in environment; refusing to run'
      ));
    }

    const child = spawn(bin, args, {
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true
    });

    let stdoutBytes = 0;
    const stdoutChunks = [];
    const stderrChunks = [];
    let killedForSize = false;

    child.stdout.on('data', chunk => {
      stdoutBytes += chunk.length;
      if (stdoutBytes > MAX_OUT_BYTES) {
        killedForSize = true;
        child.kill('SIGKILL');
        return;
      }
      stdoutChunks.push(chunk);
    });
    child.stderr.on('data', chunk => stderrChunks.push(chunk));

    const killTimer = setTimeout(() => {
      child.kill('SIGTERM');
      setTimeout(() => child.kill('SIGKILL'), 5000);
    }, timeoutMs);

    child.on('error', err => {
      clearTimeout(killTimer);
      reject(new LegalOpsError(`spawn failed: ${err.message}`));
    });

    child.on('close', code => {
      clearTimeout(killTimer);
      const stderr = Buffer.concat(stderrChunks).toString('utf8');
      if (killedForSize) {
        return reject(new LegalOpsError(
          `legalops output exceeded ${MAX_OUT_BYTES} bytes`,
          { code, stderr }
        ));
      }
      if (code !== 0) {
        return reject(new LegalOpsError(
          `legalops exit ${code}`,
          { code, stderr: stderr.slice(0, 2000) }
        ));
      }
      const stdout = Buffer.concat(stdoutChunks).toString('utf8');
      try { resolve(JSON.parse(stdout)); }
      catch { resolve({ raw: stdout }); }
    });

    if (opts.stdin) child.stdin.end(opts.stdin);
    else child.stdin.end();
  });
}

// Convenience wrappers
function health({ format = 'json' } = {}) {
  return runLegalops(['health', '--format', format]);
}
function pipeline({ text, parte = 'particular', hoje, sender = '', auditDb }) {
  const args = ['pipeline', '--parte', parte];
  if (hoje) args.push('--hoje', hoje);
  if (sender) args.push('--sender', sender);
  if (auditDb) args.push('--audit-db', auditDb);
  return runLegalops(args, { stdin: text });
}
function redact({ text, json = true }) {
  const args = ['redact'];
  if (json) args.push('--json');
  return runLegalops(args, { stdin: text });
}
function parse({ text }) {
  return runLegalops(['parse'], { stdin: text });
}
function contract({ text, skipRedact = false }) {
  const args = ['contract'];
  if (skipRedact) args.push('--skip-redact');
  return runLegalops(args, { stdin: text });
}
function dsar({ text, requestId, titularRef, direito, recebimento, hoje, skipRedact = false }) {
  const args = ['dsar', '--request-id', requestId, '--titular-ref', titularRef];
  if (direito) args.push('--direito', direito);
  if (recebimento) args.push('--recebimento', recebimento);
  if (hoje) args.push('--hoje', hoje);
  if (skipRedact) args.push('--skip-redact');
  return runLegalops(args, { stdin: text });
}
function auditVerify({ db }) {
  return runLegalops(['audit', 'verify', '--db', db]);
}
function auditList({ db }) {
  return runLegalops(['audit', 'list', '--db', db]);
}

module.exports = {
  runLegalops, LegalOpsError,
  health, pipeline, redact, parse, contract, dsar,
  auditVerify, auditList,
  // exposed for tests
  buildEnv, MAX_OUT_BYTES
};
