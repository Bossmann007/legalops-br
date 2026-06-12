'use strict';
/* global MAF, window */
// Prazos view — lista + filtros por área/urgência.

MAF.register('prazos', async function renderPrazos() {
  const wrap = MAF.el('div', { class: 'stack' });

  // Head
  const head = MAF.el('header', { class: 'view-head' });
  head.appendChild(MAF.el('div', { class: 'view-head__title', children: [
    MAF.el('h1', { text: 'Prazos processuais' }),
    MAF.el('p', { text: 'Cálculo CPC dias úteis + alertas cor-codificados' })
  ]}));
  head.appendChild(MAF.el('div', { class: 'view-head__actions', children: [
    MAF.el('button', { class: 'btn', text: '+ Manual', onClick: () => MAF.openView('intimacoes') }),
    MAF.el('button', { class: 'btn btn--ghost btn--sm', text: 'Atualizar', onClick: () => MAF.openView('prazos') })
  ]}));
  wrap.appendChild(head);

  // Filtros
  const filters = MAF.el('div', { class: 'card card--paper' });
  const filtersBody = MAF.el('div', { class: 'hstack' });
  const sel = MAF.el('select');
  sel.appendChild(new Option('Todas urgências', ''));
  sel.appendChild(new Option('Urgentes (<3 dias)', 'urgent'));
  sel.appendChild(new Option('Atenção (3-7 dias)', 'warning'));
  sel.appendChild(new Option('OK (>7 dias)', 'ok'));
  sel.appendChild(new Option('Expirados', 'expired'));
  filtersBody.appendChild(MAF.el('label', { children: [
    MAF.el('span', { text: 'Urgência' }), sel
  ]}));

  const areaSel = MAF.el('select');
  areaSel.appendChild(new Option('Todas áreas', ''));
  for (const a of (MAF.state.areas || [])) {
    areaSel.appendChild(new Option(a.label, a.key));
  }
  filtersBody.appendChild(MAF.el('label', { children: [
    MAF.el('span', { text: 'Área' }), areaSel
  ]}));
  filters.appendChild(filtersBody);
  wrap.appendChild(filters);

  // List
  const listCard = MAF.el('section', { class: 'card' });
  const list = MAF.el('div', { class: 'card__body' });
  list.appendChild(MAF.el('p', { class: 'loading', text: 'Carregando prazos…' }));
  listCard.appendChild(list);
  wrap.appendChild(listCard);

  // Load
  let items = [];
  try {
    const data = await MAF.fetch('/api/prazos');
    items = data.items || [];
  } catch (e) {
    MAF.clear(list);
    list.appendChild(MAF.el('p', { class: 'empty', text: 'Erro: ' + e.message }));
    return wrap;
  }

  function applyFilters() {
    const u = sel.value;
    const a = areaSel.value;
    const filtered = items.filter(it =>
      (!u || it.urgency === u) && (!a || it.area === a)
    );
    MAF.clear(list);
    if (filtered.length === 0) {
      list.appendChild(MAF.el('p', { class: 'empty', text: 'Nenhum prazo no filtro atual.' }));
      return;
    }
    for (const p of filtered) list.appendChild(renderPrazoRow(p, items, applyFilters));
  }

  sel.addEventListener('change', applyFilters);
  areaSel.addEventListener('change', applyFilters);

  // Resposta a "abrir prazos pela área X" via sidebar
  function onAreaFilter(e) {
    if (e.detail && e.detail.key) {
      areaSel.value = e.detail.key;
      applyFilters();
    }
  }
  window.addEventListener('maf:area-filter', onAreaFilter, { once: true });

  applyFilters();
  return wrap;
});

function renderPrazoRow(p, allItems, refresh) {
  const row = MAF.el('div', { class: 'prazo-row is-' + (p.urgency || 'ok') });
  const dm = MAF.fmt.dayMonth(p.dies_ad_quem);
  row.appendChild(MAF.el('div', { class: 'prazo-row__date', children: [
    MAF.el('strong', { text: dm.d }),
    MAF.el('span', { text: dm.m })
  ]}));
  const info = MAF.el('div', { class: 'prazo-row__info' });
  info.appendChild(MAF.el('strong', { text: p.numero_processo || '—' }));
  const meta = [p.tipo_ato, p.cliente_alias, p.area].filter(Boolean).join(' · ');
  info.appendChild(MAF.el('small', { text: meta }));
  row.appendChild(info);

  row.appendChild(MAF.el('div', { class: 'prazo-row__days', text:
    p.dias_uteis_restantes == null ? '—'
      : p.dias_uteis_restantes < 0 ? 'expirado'
      : p.dias_uteis_restantes + 'd úteis'
  }));

  const actions = MAF.el('div', { class: 'hstack' });
  actions.appendChild(MAF.el('button', {
    class: 'btn btn--sm btn--ghost', text: '✓ concluir',
    onClick: async (e) => {
      e.stopPropagation();
      try {
        await MAF.fetch('/api/prazos/' + p.id, {
          method: 'PATCH', body: { status: 'concluido' }
        });
        const idx = allItems.findIndex(x => x.id === p.id);
        if (idx >= 0) allItems.splice(idx, 1);
        refresh();
        MAF.toast('Prazo concluído', 'success');
      } catch (err) { MAF.toast('Erro: ' + err.message, 'error'); }
    }
  }));
  row.appendChild(actions);

  return row;
}
