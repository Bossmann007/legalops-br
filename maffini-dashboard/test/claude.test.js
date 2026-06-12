'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');

const claude = require('../server/lib/claude');

// Never hit the real API in these tests — fetch + redact are always stubbed.

test('runClaudeLegal → 501 ClaudeEgressError when ANTHROPIC_API_KEY unset', async () => {
  const prev = process.env.ANTHROPIC_API_KEY;
  delete process.env.ANTHROPIC_API_KEY;
  try {
    assert.equal(claude.isEnabled(), false);
    let fetchCalled = false;
    await assert.rejects(
      () => claude.runClaudeLegal({
        skill: 'review-contract',
        text: 'raw client text',
        deps: {
          redact: async () => { throw new Error('redact must not run'); },
          fetch: async () => { fetchCalled = true; return {}; }
        }
      }),
      (e) => {
        assert.equal(e.name, 'ClaudeEgressError');
        assert.equal(e.status, 501);
        assert.match(e.message, /ANTHROPIC_API_KEY/);
        return true;
      }
    );
    assert.equal(fetchCalled, false, 'fetch must never run without a key');
  } finally {
    if (prev !== undefined) process.env.ANTHROPIC_API_KEY = prev;
  }
});

test('redact runs BEFORE fetch and only redacted text leaves the machine', async () => {
  const prev = process.env.ANTHROPIC_API_KEY;
  process.env.ANTHROPIC_API_KEY = 'FAKE-TEST-KEY-xyz';
  try {
    const RAW = 'JOAO DA SILVA CPF 123.456.789-00 segredo';
    const REDACTED = '[NOME_aaaa] CPF [CPF_bbbb] segredo';
    const order = [];

    const redact = async ({ text }) => {
      order.push('redact');
      assert.equal(text, RAW, 'redact receives the RAW text');
      return { redacted_text: REDACTED };
    };

    let sentBody = null;
    let sentHeaders = null;
    const fetchStub = async (url, opts) => {
      order.push('fetch');
      sentHeaders = opts.headers;
      sentBody = JSON.parse(opts.body);
      return {
        ok: true,
        json: async () => ({ content: [{ type: 'text', text: 'analysis ok' }] })
      };
    };

    const result = await claude.runClaudeLegal({
      skill: 'review-contract',
      text: RAW,
      deps: { redact, fetch: fetchStub }
    });

    // Ordering proof: redact strictly precedes fetch.
    assert.deepEqual(order, ['redact', 'fetch']);

    // RAW text NEVER passed to fetch — neither user content nor anywhere in body.
    const bodyStr = JSON.stringify(sentBody);
    assert.ok(!bodyStr.includes('JOAO DA SILVA'), 'raw name leaked to fetch');
    assert.ok(!bodyStr.includes('123.456.789-00'), 'raw CPF leaked to fetch');
    assert.equal(sentBody.messages[0].content, REDACTED, 'only redacted text sent');
    assert.equal(sentBody.model, claude.MODEL);
    assert.equal(sentHeaders['anthropic-version'], '2023-06-01');
    assert.equal(sentHeaders['x-api-key'], 'FAKE-TEST-KEY-xyz');

    assert.deepEqual(result, {
      ok: true, skill: 'review-contract', model: claude.MODEL,
      output: 'analysis ok', redacted: true
    });
  } finally {
    if (prev !== undefined) process.env.ANTHROPIC_API_KEY = prev;
    else delete process.env.ANTHROPIC_API_KEY;
  }
});

test('API error → 502 ClaudeEgressError without leaking the key', async () => {
  const prev = process.env.ANTHROPIC_API_KEY;
  process.env.ANTHROPIC_API_KEY = 'FAKE-SECRET-KEY-xyz';
  try {
    const redact = async () => ({ redacted_text: 'redacted' });
    const fetchStub = async () => ({
      ok: false,
      status: 429,
      json: async () => ({ error: { message: 'rate limited' } })
    });
    await assert.rejects(
      () => claude.runClaudeLegal({ skill: 'brief', text: 'x', deps: { redact, fetch: fetchStub } }),
      (e) => {
        assert.equal(e.status, 502);
        assert.match(e.message, /429/);
        assert.ok(!e.message.includes('FAKE-SECRET-KEY-xyz'), 'key leaked in error');
        return true;
      }
    );
  } finally {
    if (prev !== undefined) process.env.ANTHROPIC_API_KEY = prev;
    else delete process.env.ANTHROPIC_API_KEY;
  }
});
