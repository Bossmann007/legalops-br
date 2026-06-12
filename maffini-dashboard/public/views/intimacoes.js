'use strict';
/* global MAF */
// Intimações — paste/upload .eml → pipeline LegalOps → preview + save.

MAF.register('intimacoes', async function renderIntimacoes() {
  const wrap = MAF.el('div', { class: 'stack' });

  // Head
  const head = MAF.el('header', { class: 'view-head' });
  head.appendChild(MAF.el('div', { class: 'view-head__title', children: [
    MAF.el('h1', { text: 'Intimações' }),
    MAF.el('p', { text: 'Cole o email ou anexe .eml — pipeline redige PII, identifica processo e calcula prazo (CPC Art. 219).' })
  ]}));
  wrap.appendChild(head);

  // Form card
  const formCard = MAF.el('section', { class: 'card' });
  formCard.appendChild(MAF.el('p', { class: 'card__title', text: 'Nova intimação' }));

  const form = MAF.el('form');
  form.appendChild(formField('Texto da intimação',
    MAF.el('textarea', { attrs: { name: 'text', placeholder: 'Cole aqui o email completo (cabeçalho + corpo)…', required: 'true' } })
  ));

  const fileField = MAF.el('input', { attrs: { type: 'file', name: 'eml', accept: '.eml,.txt,message/rfc822' } });
  form.appendChild(formField('… ou anexe um arquivo .eml', fileField));

  const row = MAF.el('div', { class: 'form-row' });
  const parteSel = MAF.el('select', { attrs: { name: 'parte' } });
  parteSel.appendChild(new Option('Particular', 'particular'));
  parteSel.appendChild(new Option('Fazenda', 'fazenda'));
  parteSel.appendChild(new Option('Ministério Público', 'mp'));
  parteSel.appendChild(new Option('Defensoria', 'defensoria'));
  row.appendChild(formField('Parte', parteSel));

  const areaSel = MAF.el('select', { attrs: { name: 'area' } });
  areaSel.appendChild(new Option('— selecionar —', ''));
  for (const a of (MAF.state.areas || [])) areaSel.appendChild(new Option(a.label, a.key));
  row.appendChild(formField('Área de atuação', areaSel));
  form.appendChild(row);

  form.appendChild(formField('Cliente (alias — não use nome real)',
    MAF.el('input', { attrs: { type: 'text', name: 'cliente_alias', placeholder: 'ex: CLI-021' } })
  ));

  const submitRow = MAF.el('div', { class: 'hstack' });
  submitRow.appendChild(MAF.el('button', { class: 'btn btn--primary', attrs: { type: 'submit' }, text: 'Processar pipeline' }));
  submitRow.appendChild(MAF.el('label', { class: 'hstack', children: [
    MAF.el('input', { attrs: { type: 'checkbox', name: 'persist', checked: 'true' } }),
    MAF.el('span', { text: 'Salvar prazos resultantes' })
  ]}));
  form.appendChild(submitRow);

  formCard.appendChild(form);
  wrap.appendChild(formCard);

  // Resultado area
  const resultBox = MAF.el('div');
  wrap.appendChild(resultBox);

  // File reader
  fileField.addEventListener('change', () => {
    const f = fileField.files && fileField.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      form.querySelector('textarea[name=text]').value = String(reader.result || '');
    };
    reader.readAsText(f, 'utf-8');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const text = String(fd.get('text') || '').trim();
    if (!text) { MAF.toast('Texto vazio', 'error'); return; }
    const body = {
      text,
      parte: fd.get('parte') || 'particular',
      area: fd.get('area') || '',
      cliente_alias: fd.get('cliente_alias') || '',
      persist_prazos: fd.get('persist') === 'on'
    };
    MAF.clear(resultBox);
    resultBox.appendChild(MAF.el('p', { class: 'loading', text: 'Rodando pipeline…' }));
    try {
      const result = await MAF.fetch('/api/intimacao/process', { method: 'POST', body });
      MAF.clear(resultBox);
      resultBox.appendChild(renderResult(result));
      MAF.toast('Pipeline OK — ' + (result.count || 0) + ' intimação(ões)', 'success');
    } catch (err) {
      MAF.clear(resultBox);
      resultBox.appendChild(MAF.el('div', { class: 'pipeline-result',
        children: [
          MAF.el('h4', { text: 'Erro no pipeline' }),
          MAF.el('p', { class: 'tag tag--urgent', text: err.message })
        ]
      }));
    }
  });

  return wrap;
});

function formField(labelText, control) {
  const f = MAF.el('div', { class: 'field' });
  f.appendChild(MAF.el('label', { text: labelText }));
  f.appendChild(control);
  return f;
}

function renderResult(result) {
  const card = MAF.el('div', { class: 'pipeline-result' });
  card.appendChild(MAF.el('h4', { text: 'Resultado pipeline' }));
  card.appendChild(MAF.el('p', { class: 'tag tag--gold', text: (result.count || 0) + ' intimação(ões) parseada(s)' }));

  if (result.results && result.results.length) {
    for (const r of result.results) {
      const sub = MAF.el('div', { class: 'card', style: { 'margin-top': '12px' } });
      sub.appendChild(MAF.el('h4', { text: r.numero_processo || '—' }));
      sub.appendChild(metaRow('Tipo', r.tipo_ato));
      sub.appendChild(metaRow('Data publicação', r.data_publicacao));
      sub.appendChild(metaRow('Prazo (dias)', r.prazo_dias));
      if (r.calc) {
        sub.appendChild(metaRow('Dies a quo', r.calc.dies_a_quo));
        sub.appendChild(metaRow('Dies ad quem', r.calc.dies_ad_quem));
        sub.appendChild(metaRow('Dias úteis restantes hoje', r.calc.dias_uteis_restantes));
        sub.appendChild(metaRow('Alerta', r.calc.alerta));
      }
      sub.appendChild(metaRow('Audit seq', r.audit_seq));
      sub.appendChild(metaRow('Matches PII', r.pii_matches));
      if (r.erros && r.erros.length) sub.appendChild(metaRow('Erros', r.erros.join('; ')));
      card.appendChild(sub);
    }
  }

  const pre = MAF.el('pre', { text: JSON.stringify(result, null, 2) });
  card.appendChild(MAF.el('details', { children: [
    MAF.el('summary', { text: 'JSON cru' }),
    pre
  ]}));
  return card;
}

function metaRow(k, v) {
  const r = MAF.el('div', { class: 'hstack' });
  r.appendChild(MAF.el('span', { class: 'metric__label', text: k + ':' }));
  r.appendChild(MAF.el('span', { class: 'mono', text: v == null ? '—' : String(v) }));
  return r;
}
