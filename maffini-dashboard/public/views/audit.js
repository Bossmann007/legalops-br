'use strict';
/* global MAF */
MAF.register('audit', async function renderAudit() {
  const wrap = MAF.el('div', { class: 'stack' });
  wrap.appendChild(MAF.el('header', { class: 'view-head', children: [
    MAF.el('div', { class: 'view-head__title', children: [
      MAF.el('h1', { text: 'Audit chain' }),
      MAF.el('p', { text: 'Hash chain LegalOps · LGPD Art. 37 · HMAC-SHA256 tamper-evidence' })
    ]})
  ]}));

  const verifyCard = MAF.el('section', { class: 'card card--paper' });
  verifyCard.appendChild(MAF.el('p', { class: 'card__title', text: 'Integridade' }));
  const verifyBody = MAF.el('div', { class: 'card__body' });
  verifyBody.appendChild(MAF.el('p', { class: 'loading', text: 'Verificando…' }));
  verifyCard.appendChild(verifyBody);
  wrap.appendChild(verifyCard);

  const listCard = MAF.el('section', { class: 'card' });
  listCard.appendChild(MAF.el('p', { class: 'card__title', text: 'Entradas' }));
  const listBody = MAF.el('div', { class: 'card__body' });
  listBody.appendChild(MAF.el('p', { class: 'loading', text: 'Carregando entradas…' }));
  listCard.appendChild(listBody);
  wrap.appendChild(listCard);

  loadVerify(verifyBody);
  loadList(listBody);

  return wrap;
});

async function loadVerify(host) {
  try {
    const r = await MAF.fetch('/api/audit/verify');
    MAF.clear(host);
    const tag = MAF.el('span', { class: 'tag tag--' + (r.valid ? 'ok' : 'urgent'), text: r.valid ? 'Chain íntegra' : 'CHAIN INVÁLIDA' });
    host.appendChild(tag);
    host.appendChild(MAF.el('span', { text: '  ' + (r.entries || 0) + ' entradas' }));
  } catch (e) {
    MAF.clear(host);
    host.appendChild(MAF.el('p', { class: 'tag tag--urgent', text: 'Erro: ' + e.message }));
  }
}

async function loadList(host) {
  try {
    const r = await MAF.fetch('/api/audit/list');
    MAF.clear(host);
    if (!r.raw && (!Array.isArray(r) || r.length === 0)) {
      host.appendChild(MAF.el('p', { class: 'empty', text: 'Sem entradas no audit chain.' }));
      return;
    }
    const pre = MAF.el('pre', { text: r.raw || JSON.stringify(r, null, 2) });
    host.appendChild(pre);
  } catch (e) {
    MAF.clear(host);
    host.appendChild(MAF.el('p', { class: 'tag tag--urgent', text: 'Erro: ' + e.message }));
  }
}
