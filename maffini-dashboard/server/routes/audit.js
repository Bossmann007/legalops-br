'use strict';
const { send, sendError } = require('../lib/router');
const legalops = require('../lib/legalops');

module.exports = function auditRoutes(cfg) {
  return {
    'GET /api/audit/verify': async (req, res) => {
      try {
        const result = await legalops.auditVerify({ db: cfg.paths.auditDb });
        send(res, 200, result);
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    },
    'GET /api/audit/list': async (req, res) => {
      try {
        const result = await legalops.auditList({ db: cfg.paths.auditDb });
        send(res, 200, result);
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    }
  };
};
