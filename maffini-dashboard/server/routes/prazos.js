'use strict';
const { send, sendError, readJson } = require('../lib/router');
const { JSONStore } = require('../lib/store');

function urgency(diasUteisRestantes, thresholds) {
  if (diasUteisRestantes == null) return 'unknown';
  if (diasUteisRestantes < 0) return 'expired';
  if (diasUteisRestantes <= thresholds.urgentDays) return 'urgent';
  if (diasUteisRestantes <= thresholds.warningDays) return 'warning';
  return 'ok';
}

function workingDaysBetween(from, to) {
  if (!(from instanceof Date) || !(to instanceof Date)) return null;
  if (to < from) return -workingDaysBetween(to, from);
  let count = 0;
  const cursor = new Date(from);
  cursor.setHours(0, 0, 0, 0);
  const end = new Date(to);
  end.setHours(0, 0, 0, 0);
  while (cursor < end) {
    cursor.setDate(cursor.getDate() + 1);
    const dow = cursor.getDay();
    if (dow !== 0 && dow !== 6) count += 1;
  }
  return count;
}

function icsStamp(d) {
  return d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
}
function icsDateOnly(iso) {
  return iso.slice(0, 10).replace(/-/g, '');
}
function icsNextDay(iso) {
  const d = new Date(iso + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + 1);
  return icsDateOnly(d.toISOString());
}
function icsEscape(s) {
  return String(s || '').replace(/\\/g, '\\\\').replace(/,/g, '\\,').replace(/;/g, '\\;').replace(/\n/g, '\\n');
}
function icsFold(line) {
  // RFC 5545: fold at 75 octets; don't split multi-byte UTF-8 sequences.
  const buf = Buffer.from(line, 'utf8');
  if (buf.length <= 75) return line;
  const parts = [];
  let pos = 0;
  let first = true;
  while (pos < buf.length) {
    let end = pos + (first ? 75 : 74); // continuation lines: 1 byte for leading SP
    while (end < buf.length && (buf[end] & 0xC0) === 0x80) end--;
    parts.push(buf.slice(pos, end).toString('utf8'));
    pos = end;
    first = false;
  }
  return parts.join('\r\n ');
}

function decoratePrazo(p, today, thresholds) {
  const ad_quem = p.dies_ad_quem ? new Date(p.dies_ad_quem) : null;
  const dias = ad_quem ? workingDaysBetween(today, ad_quem) : null;
  return Object.assign({}, p, {
    dias_uteis_restantes: dias,
    urgency: urgency(dias, thresholds)
  });
}

module.exports = function prazosRoutes(cfg) {
  const store = new JSONStore(cfg.paths.prazosStore);

  return {
    'GET /api/prazos': (req, res) => {
      try {
        const today = new Date();
        const items = store.list().map(p => decoratePrazo(p, today, cfg.prazoThresholds));
        items.sort((a, b) => {
          const ax = a.dies_ad_quem || '9999-12-31';
          const bx = b.dies_ad_quem || '9999-12-31';
          return ax < bx ? -1 : ax > bx ? 1 : 0;
        });
        send(res, 200, { count: items.length, items });
      } catch (e) {
        sendError(res, 500, e.message);
      }
    },

    'POST /api/prazos': async (req, res) => {
      try {
        const body = await readJson(req);
        if (!body.numero_processo) return sendError(res, 400, 'numero_processo required');
        if (!body.dies_ad_quem) return sendError(res, 400, 'dies_ad_quem required (ISO date)');
        const item = store.create({
          numero_processo: body.numero_processo,
          cliente_alias: body.cliente_alias || '',
          area: body.area || '',
          tipo_ato: body.tipo_ato || 'manual',
          parte: body.parte || 'particular',
          dies_a_quo: body.dies_a_quo || null,
          dies_ad_quem: body.dies_ad_quem,
          prazo_dias: body.prazo_dias || null,
          fundamentos: body.fundamentos || [],
          nota: body.nota || '',
          status: 'aberto',
          source: body.source || 'manual'
        });
        send(res, 201, item);
      } catch (e) {
        sendError(res, 400, e.message);
      }
    },

    'PATCH /api/prazos/:id': async (req, res, params) => {
      try {
        const body = await readJson(req);
        const item = store.update(params.id, body);
        if (!item) return sendError(res, 404, 'not found');
        send(res, 200, item);
      } catch (e) {
        sendError(res, 400, e.message);
      }
    },

    'DELETE /api/prazos/:id': (req, res, params) => {
      const ok = store.remove(params.id);
      if (!ok) return sendError(res, 404, 'not found');
      send(res, 204, '');
    },

    'GET /api/prazos/export.ics': (req, res) => {
      try {
        const dtstamp = icsStamp(new Date());
        const lines = [
          'BEGIN:VCALENDAR',
          'VERSION:2.0',
          'PRODID:-//Maffini & Rangel//LegalOps BR//PT',
          'CALSCALE:GREGORIAN',
          'METHOD:PUBLISH'
        ];
        for (const p of store.list()) {
          if (!p.dies_ad_quem || p.status === 'concluido') continue;
          const summary = 'Prazo: ' + (p.numero_processo || p.tipo_ato || '—');
          const desc = [p.tipo_ato, p.cliente_alias, p.area, p.nota].filter(Boolean).join(' · ');
          lines.push('BEGIN:VEVENT');
          lines.push('UID:' + p.id + '@maffini-dashboard');
          lines.push('DTSTAMP:' + dtstamp);
          lines.push('DTSTART;VALUE=DATE:' + icsDateOnly(p.dies_ad_quem));
          lines.push('DTEND;VALUE=DATE:' + icsNextDay(p.dies_ad_quem));
          lines.push(icsFold('SUMMARY:' + icsEscape(summary)));
          if (desc) lines.push(icsFold('DESCRIPTION:' + icsEscape(desc)));
          lines.push('END:VEVENT');
        }
        lines.push('END:VCALENDAR');
        const body = lines.join('\r\n') + '\r\n';
        res.writeHead(200, {
          'Content-Type': 'text/calendar; charset=utf-8',
          'Content-Disposition': 'attachment; filename="prazos.ics"'
        });
        res.end(body);
      } catch (e) {
        sendError(res, 500, e.message);
      }
    }
  };
};
