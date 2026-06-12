'use strict';
/* global MAF, window */
// Home view — saudação + métricas + próximos prazos urgentes.

MAF.register('home', async function renderHome() {
  const wrap = MAF.el('div', { class: 'stack' });

  // Greeting
  const owner = (MAF.state.brand && MAF.state.brand.owner) || 'Dra. Maylin';
  const tagline = (MAF.state.brand && MAF.state.brand.tagline) || '';
  const greet = MAF.el('div', { class: 'greeting' });
  greet.appendChild(MAF.el('h1', { text: MAF.fmt.saudacao() + ', ' + owner + '.' }));
  greet.appendChild(MAF.el('p', { class: 'sub', text: tagline }));
  greet.appendChild(MAF.el('button', {
    class: 'btn btn--gold cmd-cta',
    text: '⌘  Abrir central de comandos',
    onClick: () => MAF.openView('commands')
  }));
  wrap.appendChild(greet);

  // Métricas grid
  const grid = MAF.el('div', { class: 'home-grid' });

  // Bloco esquerdo — Próximos prazos
  const prazosCard = MAF.el('section', { class: 'card', attrs: { 'aria-label': 'Próximos prazos' } });
  const head = MAF.el('div', { class: 'card__head' });
  head.appendChild(MAF.el('h3', { class: 'card__title', text: 'Próximos prazos' }));
  const linkAll = MAF.el('button', { class: 'btn btn--ghost btn--sm', text: 'Ver todos →', onClick: () => MAF.openView('prazos') });
  head.appendChild(linkAll);
  prazosCard.appendChild(head);
  const list = MAF.el('div', { class: 'card__body' });
  list.appendChild(MAF.el('p', { class: 'loading', text: 'Carregando…' }));
  prazosCard.appendChild(list);
  grid.appendChild(prazosCard);

  // Bloco direito — métricas + ações
  const right = MAF.el('div', { class: 'stack' });

  const inboxCard = MAF.el('section', { class: 'card card--paper' });
  inboxCard.appendChild(MAF.el('p', { class: 'card__title', text: 'Inbox' }));
  inboxCard.appendChild(MAF.el('div', { class: 'metric', children: [
    MAF.el('span', { class: 'metric__value', text: '—' }),
    MAF.el('span', { class: 'metric__label', text: 'intimações pendentes' })
  ]}));
  inboxCard.appendChild(MAF.el('button', {
    class: 'btn btn--gold', text: 'Processar nova intimação',
    onClick: () => MAF.openView('intimacoes')
  }));
  right.appendChild(inboxCard);

  const healthCard = MAF.el('section', { class: 'card' });
  healthCard.appendChild(MAF.el('p', { class: 'card__title', text: 'Saúde do sistema' }));
  const healthBody = MAF.el('div', { class: 'card__body stack' });
  healthBody.appendChild(MAF.el('p', { class: 'loading', text: 'Verificando…' }));
  healthCard.appendChild(healthBody);
  right.appendChild(healthCard);

  grid.appendChild(right);
  wrap.appendChild(grid);

  // Async carregamento — substitui placeholders.
  loadPrazos(list);
  loadHealth(healthBody);

  return wrap;
});

async function loadPrazos(host) {
  try {
    const data = await MAF.fetch('/api/prazos');
    MAF.clear(host);
    if (!data.items || data.items.length === 0) {
      host.appendChild(MAF.el('p', { class: 'empty', text: 'Sem prazos cadastrados. Use "Intimações" para processar uma nova.' }));
      return;
    }
    const top = data.items.slice(0, 5);
    for (const p of top) host.appendChild(renderPrazoRow(p));
  } catch (e) {
    MAF.clear(host);
    host.appendChild(MAF.el('p', { class: 'empty', text: 'Erro: ' + e.message }));
  }
}

function renderPrazoRow(p) {
  const row = MAF.el('div', { class: 'prazo-row is-' + (p.urgency || 'ok') });
  const dm = MAF.fmt.dayMonth(p.dies_ad_quem);
  const date = MAF.el('div', { class: 'prazo-row__date', children: [
    MAF.el('strong', { text: dm.d }),
    MAF.el('span', { text: dm.m })
  ]});
  const info = MAF.el('div', { class: 'prazo-row__info' });
  info.appendChild(MAF.el('strong', { text: p.numero_processo || '—' }));
  info.appendChild(MAF.el('small', { text: [p.tipo_ato, p.cliente_alias].filter(Boolean).join(' · ') }));
  const days = MAF.el('div', { class: 'prazo-row__days', text:
    p.dias_uteis_restantes == null ? '—'
      : p.dias_uteis_restantes < 0 ? 'expirado'
      : p.dias_uteis_restantes + 'd úteis'
  });
  const tag = MAF.el('span', {
    class: 'tag tag--' + (p.urgency === 'urgent' ? 'urgent' : p.urgency === 'warning' ? 'warning' : 'ok'),
    text: p.urgency === 'urgent' ? 'urgente' : p.urgency === 'warning' ? 'atenção' : 'ok'
  });
  row.appendChild(date);
  row.appendChild(info);
  row.appendChild(days);
  row.appendChild(tag);
  return row;
}

async function loadHealth(host) {
  try {
    const h = await MAF.fetch('/api/health');
    MAF.clear(host);
    const checks = (h.legalops && h.legalops.checks) || [];
    if (checks.length === 0) {
      host.appendChild(MAF.el('p', { text: 'Sem dados.' }));
      return;
    }
    for (const c of checks) {
      const tag = MAF.el('span', { class: 'tag tag--' + (c.ok ? 'ok' : 'urgent'), text: c.ok ? 'OK' : 'falha' });
      host.appendChild(MAF.el('div', { class: 'hstack', children: [
        tag,
        MAF.el('span', { text: c.name + ' (' + c.ms + ' ms)' })
      ]}));
    }
  } catch (e) {
    MAF.clear(host);
    host.appendChild(MAF.el('p', { class: 'tag tag--urgent', text: 'Erro: ' + e.message }));
  }
}
