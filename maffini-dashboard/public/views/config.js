'use strict';
/* global MAF */
MAF.register('config', async function renderConfig() {
  const wrap = MAF.el('div', { class: 'stack' });
  wrap.appendChild(MAF.el('header', { class: 'view-head', children: [
    MAF.el('div', { class: 'view-head__title', children: [
      MAF.el('h1', { text: 'Configurações' }),
      MAF.el('p', { text: 'Brand · canais de notificação · auth' })
    ]})
  ]}));

  const card = MAF.el('section', { class: 'card' });
  card.appendChild(MAF.el('p', { class: 'card__title', text: 'Marca' }));
  const body = MAF.el('div', { class: 'card__body stack' });
  const b = MAF.state.brand || {};
  body.appendChild(MAF.el('p', { children: [
    MAF.el('strong', { text: 'Nome: ' }),
    MAF.el('span', { text: b.name || '—' })
  ]}));
  body.appendChild(MAF.el('p', { children: [
    MAF.el('strong', { text: 'Tagline: ' }),
    MAF.el('span', { text: b.tagline || '—' })
  ]}));
  body.appendChild(MAF.el('p', { children: [
    MAF.el('strong', { text: 'Site: ' }),
    MAF.el('span', { text: b.site || '—' })
  ]}));
  body.appendChild(MAF.el('p', { children: [
    MAF.el('strong', { text: 'WhatsApp: ' }),
    MAF.el('span', { text: b.whatsapp || '—' })
  ]}));
  body.appendChild(MAF.el('p', { class: 'mono', text: 'Editar via maffini.config.json (server-side) — UI de edição em v0.2.' }));
  card.appendChild(body);
  wrap.appendChild(card);

  return wrap;
});
