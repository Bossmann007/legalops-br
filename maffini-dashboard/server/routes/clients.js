'use strict';
const { send, sendError, readJson } = require('../lib/router');
const { JSONStore } = require('../lib/store');

module.exports = function clientsRoutes(cfg) {
  const store = new JSONStore(cfg.paths.clientsStore);

  return {
    'GET /api/clients': (req, res) => {
      send(res, 200, { count: store.list().length, items: store.list() });
    },
    'POST /api/clients': async (req, res) => {
      try {
        const body = await readJson(req);
        if (!body.alias) return sendError(res, 400, 'alias required (use placeholder, not real name)');
        const item = store.create({
          alias: body.alias,
          area: body.area || '',
          contato_redacted: body.contato_redacted || '',
          processos: Array.isArray(body.processos) ? body.processos : [],
          notas: body.notas || ''
        });
        send(res, 201, item);
      } catch (e) { sendError(res, 400, e.message); }
    },
    'PATCH /api/clients/:id': async (req, res, params) => {
      try {
        const body = await readJson(req);
        const item = store.update(params.id, body);
        if (!item) return sendError(res, 404, 'not found');
        send(res, 200, item);
      } catch (e) { sendError(res, 400, e.message); }
    },
    'DELETE /api/clients/:id': (req, res, params) => {
      const ok = store.remove(params.id);
      if (!ok) return sendError(res, 404, 'not found');
      send(res, 204, '');
    }
  };
};
