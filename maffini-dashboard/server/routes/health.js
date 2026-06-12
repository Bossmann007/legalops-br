'use strict';
const { send, sendError } = require('../lib/router');
const legalops = require('../lib/legalops');

module.exports = function healthRoutes(cfg) {
  return {
    'GET /api/health': async (req, res) => {
      try {
        const result = await legalops.health();
        send(res, 200, {
          dashboard: { ok: true, version: require('../../package.json').version },
          legalops: result
        });
      } catch (e) {
        sendError(res, 500, e.message, { stderr: e.stderr });
      }
    },

    'GET /api/brand': (req, res) => {
      send(res, 200, {
        brand: cfg.brand,
        areas: cfg.areas,
        prazoThresholds: cfg.prazoThresholds
      });
    }
  };
};
