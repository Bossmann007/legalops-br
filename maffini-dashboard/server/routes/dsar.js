'use strict';
const { send, sendError, readJson } = require('../lib/router');
const legalops = require('../lib/legalops');
const { JSONStore } = require('../lib/store');
const path = require('path');

module.exports = function dsarRoutes(cfg) {
  const file = path.join(path.dirname(cfg.paths.prazosStore), 'dsars.json');
  const store = new JSONStore(file);

  return {
    'GET /api/dsar': (req, res) => {
      send(res, 200, { count: store.list().length, items: store.list() });
    },

    'POST /api/dsar/process': async (req, res) => {
      try {
        const body = await readJson(req);
        if (!body.text) return sendError(res, 400, 'text required');
        if (!body.request_id) return sendError(res, 400, 'request_id required');
        if (!body.titular_ref) return sendError(res, 400, 'titular_ref required (hash, NOT real name)');
        const result = await legalops.dsar({
          text: body.text,
          requestId: body.request_id,
          titularRef: body.titular_ref,
          direito: body.direito,
          recebimento: body.recebimento,
          hoje: body.hoje,
          skipRedact: Boolean(body.skip_redact)
        });
        if (result && result.request_id) {
          store.create({
            request_id: result.request_id,
            codigo_direito: result.codigo_direito,
            artigo: result.artigo,
            prazo_final: result.prazo_final,
            dias_restantes: result.dias_restantes,
            status: result.status,
            titular_ref: body.titular_ref
          });
        }
        send(res, 200, result);
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    }
  };
};
