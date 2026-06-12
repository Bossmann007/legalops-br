'use strict';
/* global MAF */
// Central de comandos — Tia May roda tudo por clique. Nada executa sem
// autorização explícita (ver MAF.confirmCommand no _shared.js).

MAF.register('commands', async function renderCommands() {
  const wrap = MAF.el('div', { class: 'stack' });

  // Head
  const head = MAF.el('header', { class: 'view-head' });
  head.appendChild(MAF.el('div', { class: 'view-head__title', children: [
    MAF.el('h1', { text: 'Central de Comandos' }),
    MAF.el('p', { text: 'Clique em um comando para revisar e autorizar a execução. Nada roda sem sua confirmação.' })
  ]}));
  wrap.appendChild(head);

  const catalog = await MAF.fetch('/api/command/list');
  const groups = (catalog.groups || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0));
  const commands = catalog.commands || [];

  // Area filter chips
  const chipBar = MAF.el('div', { class: 'cmd-chips' });
  const sections = MAF.el('div', { class: 'cmd-sections' });
  let activeArea = null;

  function chip(key, label) {
    const c = MAF.el('button', {
      class: 'chip' + ((activeArea === key) ? ' is-active' : ''),
      attrs: { type: 'button' },
      text: label
    });
    c.addEventListener('click', () => { activeArea = key; renderSections(); });
    return c;
  }

  function renderChips() {
    MAF.clear(chipBar);
    chipBar.appendChild(chip(null, 'Todas'));
    for (const a of (MAF.state.areas || [])) chipBar.appendChild(chip(a.key, a.label));
  }

  function renderSections() {
    renderChips();
    MAF.clear(sections);
    const filtered = activeArea
      ? commands.filter(c => Array.isArray(c.areas) && c.areas.includes(activeArea))
      : commands;

    if (filtered.length === 0) {
      sections.appendChild(MAF.el('p', { class: 'empty', text: 'Nenhum comando para esta área.' }));
      return;
    }

    const ordered = groups.length ? groups : inferGroups(filtered);
    for (const g of ordered) {
      const inGroup = filtered.filter(c => c.group === g.key);
      if (inGroup.length === 0) continue;
      const sec = MAF.el('section', { class: 'cmd-group' });
      sec.appendChild(MAF.el('h2', { class: 'cmd-group__title', text: g.label || g.key }));
      const grid = MAF.el('div', { class: 'cmd-grid' });
      for (const cmd of inGroup) grid.appendChild(commandCard(cmd));
      sec.appendChild(grid);
      sections.appendChild(sec);
    }
  }

  wrap.appendChild(chipBar);
  wrap.appendChild(sections);
  renderSections();
  return wrap;
});

function inferGroups(commands) {
  const seen = [];
  for (const c of commands) if (!seen.find(g => g.key === c.group)) seen.push({ key: c.group, label: c.group });
  return seen;
}

function commandCard(cmd) {
  const card = MAF.el('button', { class: 'cmd-card', attrs: { type: 'button' } });

  const top = MAF.el('div', { class: 'cmd-card__top' });
  top.appendChild(MAF.el('span', { class: 'cmd-card__icon', text: cmd.icon || '▤' }));
  if (cmd.requiresApproval) top.appendChild(MAF.el('span', { class: 'cmd-card__lock', text: '🔒', attrs: { title: 'Requer autorização' } }));
  if (cmd.dangerLevel === 'high' || cmd.dangerLevel === 'medium') {
    top.appendChild(MAF.el('span', {
      class: 'cmd-card__danger is-' + (cmd.dangerLevel === 'high' ? 'urgent' : 'warning'),
      text: cmd.dangerLevel === 'high' ? 'alto risco' : 'sensível'
    }));
  }
  card.appendChild(top);

  card.appendChild(MAF.el('strong', { class: 'cmd-card__label', text: cmd.label || cmd.id }));
  if (cmd.blurb) card.appendChild(MAF.el('span', { class: 'cmd-card__blurb', text: cmd.blurb }));

  card.addEventListener('click', () => MAF.confirmCommand(cmd));
  return card;
}
