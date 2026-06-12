'use strict';
/* global MAF */
MAF.register('clientes', async function renderClientes() {
  const wrap = MAF.el('div', { class: 'stack' });
  wrap.appendChild(MAF.el('header', { class: 'view-head', children: [
    MAF.el('div', { class: 'view-head__title', children: [
      MAF.el('h1', { text: 'Clientes' }),
      MAF.el('p', { text: 'Mini CRM — apenas aliases (sem PII real)' })
    ]})
  ]}));

  const card = MAF.el('section', { class: 'card' });
  card.appendChild(MAF.el('p', { class: 'card__title', text: 'Lista' }));
  const body = MAF.el('div', { class: 'card__body' });
  body.appendChild(MAF.el('p', { class: 'loading', text: 'Carregando…' }));
  card.appendChild(body);
  wrap.appendChild(card);

  try {
    const data = await MAF.fetch('/api/clients');
    MAF.clear(body);
    if (!data.items || data.items.length === 0) {
      body.appendChild(MAF.el('p', { class: 'empty', text: 'Sem clientes cadastrados.' }));
      return wrap;
    }
    const tbl = MAF.el('table', { class: 'table' });
    const thead = MAF.el('thead');
    const trh = MAF.el('tr');
    ['Alias', 'Área', 'Processos', 'Atualizado'].forEach(h => trh.appendChild(MAF.el('th', { text: h })));
    thead.appendChild(trh);
    tbl.appendChild(thead);
    const tbody = MAF.el('tbody');
    for (const c of data.items) {
      const tr = MAF.el('tr');
      tr.appendChild(MAF.el('td', { text: c.alias }));
      tr.appendChild(MAF.el('td', { text: c.area || '—' }));
      tr.appendChild(MAF.el('td', { text: (c.processos || []).length }));
      tr.appendChild(MAF.el('td', { text: MAF.fmt.dateBR(c.updatedAt || c.createdAt) }));
      tbody.appendChild(tr);
    }
    tbl.appendChild(tbody);
    body.appendChild(tbl);
  } catch (e) {
    MAF.clear(body);
    body.appendChild(MAF.el('p', { class: 'tag tag--urgent', text: 'Erro: ' + e.message }));
  }
  return wrap;
});
