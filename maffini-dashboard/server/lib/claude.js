'use strict';
// Claude-for-Legal egress — SAFE, redacted, opt-in.
//
// Segurança / LGPD (regra de ouro):
// - RAW client text NUNCA sai da máquina. Antes de qualquer chamada externa,
//   o texto passa pelo `legalops redact` e SÓ o `redacted_text` é enviado.
// - Gate em ANTHROPIC_API_KEY: sem key → 501 (não habilitado). Nunca hardcode.
// - Sem dependência nova: usa o global `fetch` do Node 20.
// - Timeout via AbortController (~30s). Erro de API → 502 sanitizado
//   (NUNCA vaza a key nem o corpo do texto).
// - Este egress continua atrás do approval gate por-comando (rota decide).

const legalops = require('./legalops');

const API_URL = 'https://api.anthropic.com/v1/messages';
const API_VERSION = '2023-06-01';
const MODEL = 'claude-sonnet-4-6';
const MAX_TOKENS = 1500;
const TIMEOUT_MS = 30_000;

// System prompt scoped per skill. Todos reforçam: texto JÁ redigido, PII mascarada.
const SYSTEM_PROMPTS = {
  'review-contract':
    'Você é assistente jurídico. Analise o texto JÁ REDIGIDO (PII mascarada como ' +
    '[TIPO_xxxx]). Identifique cláusulas relevantes, riscos e desvios. Não invente dados.',
  'triage-nda':
    'Você é assistente jurídico. Triagem de NDA sobre texto JÁ REDIGIDO (PII mascarada ' +
    'como [TIPO_xxxx]). Classifique risco e recomende. Não invente dados.',
  'compliance-check':
    'Você é assistente jurídico de compliance. Avalie o texto JÁ REDIGIDO (PII mascarada ' +
    'como [TIPO_xxxx]) contra a regulação aplicável. Não invente dados.',
  'legal-risk-assessment':
    'Você é assistente jurídico. Avalie risco jurídico do texto JÁ REDIGIDO (PII mascarada ' +
    'como [TIPO_xxxx]) por severidade e probabilidade. Não invente dados.',
  'vendor-check':
    'Você é assistente jurídico. Due diligence de fornecedor sobre texto JÁ REDIGIDO ' +
    '(PII mascarada como [TIPO_xxxx]). Não invente dados.',
  'brief':
    'Você é assistente jurídico. Gere memorial/brief a partir do texto JÁ REDIGIDO ' +
    '(PII mascarada como [TIPO_xxxx]). Não invente dados.',
  'legal-response':
    'Você é assistente jurídico. Minute resposta jurídica para o texto JÁ REDIGIDO ' +
    '(PII mascarada como [TIPO_xxxx]). Não invente dados.',
  'meeting-briefing':
    'Você é assistente jurídico. Prepare briefing pré-reunião do texto JÁ REDIGIDO ' +
    '(PII mascarada como [TIPO_xxxx]). Não invente dados.',
  'signature-request':
    'Você é assistente jurídico. Prepare pedido de assinatura a partir do texto JÁ REDIGIDO ' +
    '(PII mascarada como [TIPO_xxxx]). Não invente dados.'
};

const DEFAULT_SYSTEM =
  'Você é assistente jurídico. Analise o texto JÁ REDIGIDO (PII mascarada como ' +
  '[TIPO_xxxx]). Não invente dados.';

class ClaudeEgressError extends Error {
  constructor(message, { status } = {}) {
    super(message);
    this.name = 'ClaudeEgressError';
    this.status = status; // HTTP status the route should emit
  }
}

function apiKey() {
  const k = process.env.ANTHROPIC_API_KEY;
  return (typeof k === 'string' && k.trim() !== '') ? k.trim() : null;
}

function isEnabled() {
  return apiKey() !== null;
}

/**
 * Run a Claude-for-Legal skill on `rawText`.
 *
 * MANDATORY: redacts `rawText` via the legalops bridge BEFORE any network call.
 * Only the redacted text leaves the machine.
 *
 * @param {object} opts
 * @param {string} opts.skill   skill key (e.g. 'review-contract')
 * @param {string} opts.text    RAW client text (redacted before egress)
 * @param {object} [opts.deps]  injectable deps for tests: { redact, fetch }
 * @returns {Promise<{ok, skill, model, output, redacted}>}
 * @throws {ClaudeEgressError} with .status for the route (501/502)
 */
async function runClaudeLegal({ skill, text, deps = {} }) {
  const redactFn = deps.redact || legalops.redact;
  const fetchFn = deps.fetch || globalThis.fetch;

  const key = apiKey();
  if (!key) {
    throw new ClaudeEgressError(
      'defina ANTHROPIC_API_KEY para habilitar Claude for Legal',
      { status: 501 }
    );
  }

  // ── MANDATORY redaction BEFORE any egress ──────────────────────────────
  // RAW text must never reach the fetch call. We extract `redacted_text`.
  const redaction = await redactFn({ text: String(text == null ? '' : text), json: true });
  const redactedText = redaction && typeof redaction.redacted_text === 'string'
    ? redaction.redacted_text
    : null;
  if (redactedText === null) {
    throw new ClaudeEgressError(
      'falha na redação PII — egress abortado',
      { status: 502 }
    );
  }

  const system = SYSTEM_PROMPTS[skill] || DEFAULT_SYSTEM;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let resp;
  try {
    resp = await fetchFn(API_URL, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'x-api-key': key,
        'anthropic-version': API_VERSION,
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: MAX_TOKENS,
        system,
        messages: [{ role: 'user', content: redactedText }]
      })
    });
  } catch (e) {
    clearTimeout(timer);
    const why = e && e.name === 'AbortError' ? 'timeout' : 'falha de rede';
    throw new ClaudeEgressError(`Claude egress: ${why}`, { status: 502 });
  }
  clearTimeout(timer);

  if (!resp.ok) {
    // Never leak the key or raw text. Surface only status + provider message.
    let providerMsg = '';
    try {
      const errBody = await resp.json();
      providerMsg = errBody && errBody.error && errBody.error.message
        ? String(errBody.error.message) : '';
    } catch { /* ignore parse error */ }
    throw new ClaudeEgressError(
      `Claude API ${resp.status}${providerMsg ? `: ${providerMsg}` : ''}`,
      { status: 502 }
    );
  }

  const data = await resp.json();
  const output = Array.isArray(data.content)
    ? data.content.filter(b => b.type === 'text').map(b => b.text).join('\n')
    : '';

  return { ok: true, skill, model: MODEL, output, redacted: true };
}

module.exports = {
  runClaudeLegal,
  isEnabled,
  ClaudeEgressError,
  // exposed for tests
  SYSTEM_PROMPTS,
  MODEL
};
