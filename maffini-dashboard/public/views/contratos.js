'use strict';
/* global MAF */
MAF.register('contratos', async function renderContratos() {
  const wrap = MAF.el('div', { class: 'stack' });
  wrap.appendChild(MAF.el('header', { class: 'view-head', children: [
    MAF.el('div', { class: 'view-head__title', children: [
      MAF.el('h1', { text: 'Contratos' }),
      MAF.el('p', { text: 'Analisa risco — cláusulas abusivas CDC + financiamento (LegalOps Contract AI v1.2)' })
    ]})
  ]}));

  const form = MAF.el('form', { class: 'card' });
  form.appendChild(MAF.el('p', { class: 'card__title', text: 'Análise de contrato' }));
  const ta = MAF.el('textarea', { attrs: { placeholder: 'Cole o texto do contrato…', required: 'true' } });
  form.appendChild(ta);
  form.appendChild(MAF.el('div', { class: 'hstack', style: { 'margin-top': '12px' }, children: [
    MAF.el('button', { class: 'btn btn--primary', attrs: { type: 'submit' }, text: 'Analisar' })
  ]}));
  wrap.appendChild(form);

  const out = MAF.el('div');
  wrap.appendChild(out);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = ta.value.trim();
    if (!text) return;
    MAF.clear(out);
    out.appendChild(MAF.el('p', { class: 'loading', text: 'Analisando…' }));
    try {
      const r = await MAF.fetch('/api/contract/analyze', { method: 'POST', body: { text } });
      MAF.clear(out);
      const card = MAF.el('div', { class: 'pipeline-result' });
      card.appendChild(MAF.el('h4', { text: 'Resultado' }));
      card.appendChild(MAF.el('p', { children: [
        MAF.el('span', { class: 'tag tag--' + (r.nivel === 'alto' ? 'urgent' : r.nivel === 'medio' ? 'warning' : 'ok'), text: 'Risco ' + (r.nivel || '—') }),
        MAF.el('span', { class: 'mono', text: ' · score ' + (r.score == null ? '—' : r.score) })
      ]}));
      if (r.clausulas && r.clausulas.length) {
        card.appendChild(MAF.el('h4', { text: 'Cláusulas detectadas' }));
        const ul = MAF.el('ul');
        for (const c of r.clausulas) ul.appendChild(MAF.el('li', { text: typeof c === 'string' ? c : JSON.stringify(c) }));
        card.appendChild(ul);
      }
      if (r.recomendacoes && r.recomendacoes.length) {
        card.appendChild(MAF.el('h4', { text: 'Recomendações' }));
        const ul = MAF.el('ul');
        for (const rec of r.recomendacoes) ul.appendChild(MAF.el('li', { text: rec }));
        card.appendChild(ul);
      }
      out.appendChild(card);
    } catch (err) {
      MAF.clear(out);
      out.appendChild(MAF.el('p', { class: 'tag tag--urgent', text: 'Erro: ' + err.message }));
    }
  });

  return wrap;
});
