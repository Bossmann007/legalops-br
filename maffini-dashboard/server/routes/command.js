'use strict';
// Command execution + approval backbone.
//
// GET  /api/command/list — PUBLIC. Returns { groups, commands } from registry.
// POST /api/command/run  — AUTH. Dispatches a command by exec.kind, enforcing
//                          server-side approval and writing an approval record.
//
// Segurança / LGPD:
// - Approval é checada no servidor; cliente NUNCA pode pular o gate.
// - inputs_hash = SHA-256 do JSON dos inputs SEM campos redactable (nunca PII raw).
// - claude_legal (egress LLM) fica gated — 501, sem caminho de saída implementado.
// - args sempre array; __AUDIT_DB__ placeholder resolvido pra cfg.paths.auditDb.

const path = require('path');
const crypto = require('crypto');
const { send, sendError, readJson } = require('../lib/router');
const legalops = require('../lib/legalops');
const claude = require('../lib/claude');
const { JSONStore } = require('../lib/store');
const { GROUPS, catalog, getById } = require('../lib/commands');

// Hash inputs after stripping every registry field marked redactable:true.
// Never persists raw PII — only a deterministic digest of the non-sensitive rest.
function inputsHash(cmd, inputs) {
  const redactable = new Set(
    (cmd.inputs || []).filter(i => i.redactable).map(i => i.key)
  );
  const safe = {};
  for (const k of Object.keys(inputs || {})) {
    if (redactable.has(k)) continue;
    safe[k] = inputs[k];
  }
  return crypto.createHash('sha256')
    .update(JSON.stringify(safe))
    .digest('hex');
}

module.exports = function commandRoutes(cfg) {
  const prazosStore = new JSONStore(cfg.paths.prazosStore);
  // No `audit append` subcommand exists in the legalops CLI (only verify/list),
  // so approval records go to a local atomic JSON store in the same data/ dir.
  const approvalsStore = new JSONStore(
    path.join(path.dirname(cfg.paths.prazosStore), 'approvals.json')
  );

  function recordApproval(cmd, id, inputs) {
    return approvalsStore.create({
      command_id: id,
      action: cmd.audit ? cmd.audit.action : id,
      resource: cmd.audit ? cmd.audit.resource : '',
      timestamp: new Date().toISOString(),
      inputs_hash: inputsHash(cmd, inputs)
    });
  }

  return {
    'GET /api/command/list': async (req, res) => {
      send(res, 200, { groups: GROUPS, commands: catalog() });
    },

    'POST /api/command/run': async (req, res) => {
      try {
        const body = await readJson(req, { maxBytes: 5 * 1024 * 1024 });
        const id = body.id;
        const inputs = body.inputs || {};

        const cmd = getById(id);
        if (!cmd) return sendError(res, 404, 'unknown command');

        // Approval gate — mandatory unless registry explicitly opts out.
        const needsApproval = cmd.requiresApproval !== false;
        if (needsApproval && body.approved !== true) {
          return sendError(res, 403, 'approval required', { command: id });
        }

        // Required input validation.
        for (const i of (cmd.inputs || [])) {
          if (i.required && (inputs[i.key] === undefined ||
              inputs[i.key] === null || inputs[i.key] === '')) {
            return sendError(res, 400, `missing required input: ${i.key}`);
          }
        }

        const kind = cmd.exec.kind;

        // internal: legalops Python modules sem CLI subcommand ainda.
        if (kind === 'internal') {
          if (needsApproval) recordApproval(cmd, id, inputs);
          return send(res, 501, {
            status: 'not_implemented',
            module: cmd.exec.module,
            op: cmd.exec.op,
            note: 'CLI bridge pending — v0.2'
          });
        }

        // claude_legal: egress LLM SAFE, redacted, opt-in via ANTHROPIC_API_KEY.
        // Já passou pelo approval gate acima (needsApproval/approved). O texto
        // bruto é redigido por legalops ANTES de qualquer chamada externa.
        if (kind === 'claude_legal') {
          if (!claude.isEnabled()) {
            if (needsApproval) recordApproval(cmd, id, inputs);
            return send(res, 501, {
              status: 'not_implemented',
              skill: cmd.exec.skill,
              note: 'defina ANTHROPIC_API_KEY para habilitar Claude for Legal'
            });
          }
          const rawText = cmd.exec.stdinKey ? inputs[cmd.exec.stdinKey] : '';
          try {
            const result = await claude.runClaudeLegal({
              skill: cmd.exec.skill,
              text: rawText
            });
            const approval = needsApproval ? recordApproval(cmd, id, inputs) : null;
            return send(res, 200, {
              ok: true,
              command: id,
              approved: true,
              audit_ref: approval ? approval.id : null,
              result
            });
          } catch (e) {
            const status = (e && e.status) || 502;
            if (needsApproval) recordApproval(cmd, id, inputs);
            return send(res, status, {
              status: status === 501 ? 'not_implemented' : 'egress_error',
              skill: cmd.exec.skill,
              note: e.message
            });
          }
        }

        // legalops (notify commands also use kind 'legalops').
        if (kind === 'legalops') {
          const args = (cmd.exec.args ? cmd.exec.args(inputs) : []).map(a =>
            a === '__AUDIT_DB__' ? cfg.paths.auditDb : a
          );
          const stdin = cmd.exec.stdinKey ? inputs[cmd.exec.stdinKey] : undefined;
          const result = await legalops.runLegalops(args, { stdin });

          if (cmd.exec.postPersist === 'prazos' && inputs.persist && result.results) {
            for (const r of result.results) {
              if (!r.calc || !r.calc.dies_ad_quem) continue;
              prazosStore.create({
                numero_processo: r.numero_processo,
                cliente_alias: inputs.cliente_alias || '',
                area: inputs.area || '',
                tipo_ato: r.tipo_ato,
                parte: inputs.parte || 'particular',
                dies_a_quo: r.calc.dies_a_quo,
                dies_ad_quem: r.calc.dies_ad_quem,
                prazo_dias: r.calc.prazo_efetivo_dias,
                fundamentos: r.calc.fundamentos || [],
                status: 'aberto',
                source: cmd.id,
                audit_seq: r.audit_seq
              });
            }
          }

          const approval = needsApproval ? recordApproval(cmd, id, inputs) : null;
          return send(res, 200, {
            ok: true,
            command: id,
            approved: true,
            audit_ref: approval ? approval.id : null,
            result
          });
        }

        return sendError(res, 400, `unsupported exec kind: ${kind}`);
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    }
  };
};
