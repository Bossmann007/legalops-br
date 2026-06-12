'use strict';
const { send, sendError, readJson } = require('../lib/router');
const legalops = require('../lib/legalops');

module.exports = function contractRoutes(/* cfg */) {
  return {
    'POST /api/contract/analyze': async (req, res) => {
      try {
        const body = await readJson(req, { maxBytes: 5 * 1024 * 1024 });
        if (!body.text) return sendError(res, 400, 'text required');
        const result = await legalops.contract({
          text: body.text,
          skipRedact: Boolean(body.skip_redact)
        });
        send(res, 200, result);
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    }
  };
};
