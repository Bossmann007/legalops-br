'use strict';
const { send, sendError, readJson } = require('../lib/router');
const legalops = require('../lib/legalops');
const { JSONStore } = require('../lib/store');

module.exports = function intimacaoRoutes(cfg) {
  const prazosStore = new JSONStore(cfg.paths.prazosStore);

  return {
    'POST /api/intimacao/process': async (req, res) => {
      try {
        const body = await readJson(req, { maxBytes: 5 * 1024 * 1024 });
        if (!body.text || typeof body.text !== 'string') {
          return sendError(res, 400, 'text required');
        }
        const result = await legalops.pipeline({
          text: body.text,
          parte: body.parte || 'particular',
          hoje: body.hoje,
          sender: body.sender || '',
          auditDb: body.audit_db || cfg.paths.auditDb
        });
        if (body.persist_prazos && result.results) {
          for (const r of result.results) {
            if (!r.calc || !r.calc.dies_ad_quem) continue;
            prazosStore.create({
              numero_processo: r.numero_processo,
              cliente_alias: body.cliente_alias || '',
              area: body.area || '',
              tipo_ato: r.tipo_ato,
              parte: body.parte || 'particular',
              dies_a_quo: r.calc.dies_a_quo,
              dies_ad_quem: r.calc.dies_ad_quem,
              prazo_dias: r.calc.prazo_efetivo_dias,
              fundamentos: r.calc.fundamentos || [],
              status: 'aberto',
              source: 'intimacao_pipeline',
              audit_seq: r.audit_seq
            });
          }
        }
        send(res, 200, result);
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    },

    'POST /api/intimacao/redact': async (req, res) => {
      try {
        const body = await readJson(req);
        if (!body.text) return sendError(res, 400, 'text required');
        const result = await legalops.redact({ text: body.text, json: true });
        send(res, 200, result);
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    }
  };
};
