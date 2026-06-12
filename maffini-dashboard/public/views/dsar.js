'use strict';
/* global MAF */
MAF.register('dsar', async function renderDsar() {
  const wrap = MAF.el('div', { class: 'stack' });
  wrap.appendChild(MAF.el('header', { class: 'view-head', children: [
    MAF.el('div', { class: 'view-head__title', children: [
      MAF.el('h1', { text: 'DSAR LGPD' }),
      MAF.el('p', { text: 'Requisições de titular (Art. 18) · prazo Art. 19 (15 dias)' })
    ]})
  ]}));

  const form = MAF.el('form', { class: 'card' });
  form.appendChild(MAF.el('p', { class: 'card__title', text: 'Nova requisição' }));

  const reqIdField = MAF.el('div', { class: 'field' });
  reqIdField.appendChild(MAF.el('label', { text: 'Request ID (próprio · ex: REQ-2026-001)' }));
  reqIdField.appendChild(MAF.el('input', { attrs: { type: 'text', name: 'request_id', required: 'true' } }));
  form.appendChild(reqIdField);

  const titularField = MAF.el('div', { class: 'field' });
  titularField.appendChild(MAF.el('label', { text: 'Referência titular (hash — NÃO use nome real)' }));
  titularField.appendChild(MAF.el('input', { attrs: { type: 'text', name: 'titular_ref', placeholder: 'hash:abc123', required: 'true' } }));
  form.appendChild(titularField);

  const textField = MAF.el('div', { class: 'field' });
  textField.appendChild(MAF.el('label', { text: 'Texto da requisição' }));
  textField.appendChild(MAF.el('textarea', { attrs: { name: 'text', required: 'true' } }));
  form.appendChild(textField);

  form.appendChild(MAF.el('button', { class: 'btn btn--primary', attrs: { type: 'submit' }, text: 'Processar DSAR' }));
  wrap.appendChild(form);

  const out = MAF.el('div');
  wrap.appendChild(out);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = {
      request_id: fd.get('request_id'),
      titular_ref: fd.get('titular_ref'),
      text: fd.get('text')
    };
    MAF.clear(out);
    out.appendChild(MAF.el('p', { class: 'loading', text: 'Processando…' }));
    try {
      const r = await MAF.fetch('/api/dsar/process', { method: 'POST', body });
      MAF.clear(out);
      const card = MAF.el('div', { class: 'pipeline-result' });
      card.appendChild(MAF.el('h4', { text: 'Direito ' + (r.codigo_direito || '—') + ' (' + (r.artigo || 'Art. ?') + ')' }));
      const tagCls = r.status === 'urgente' ? 'urgent' : r.status === 'atrasado' ? 'urgent' : 'ok';
      card.appendChild(MAF.el('p', { children: [
        MAF.el('span', { class: 'tag tag--' + tagCls, text: r.status || '—' }),
        MAF.el('span', { class: 'mono', text: ' · prazo final ' + (r.prazo_final || '—') + ' · ' + (r.dias_restantes ?? '—') + 'd restantes' })
      ]}));
      const resp = MAF.el('pre', { text: r.texto_resposta || '—' });
      card.appendChild(MAF.el('h4', { text: 'Resposta sugerida' }));
      card.appendChild(resp);
      out.appendChild(card);
    } catch (err) {
      MAF.clear(out);
      out.appendChild(MAF.el('p', { class: 'tag tag--urgent', text: 'Erro: ' + err.message }));
    }
  });

  return wrap;
});
