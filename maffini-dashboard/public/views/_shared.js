'use strict';
/* global window, document, fetch */
// Maffini Dashboard — shared runtime.
// Define `window.MAF` namespace + helpers used by all views.

(function () {
  if (window.MAF) return;
  const MAF = {};

  MAF.api = '/api';
  MAF.state = {
    brand: null,
    areas: [],
    currentView: 'home',
    creds: null  // basic auth memory (only set after first 401 retry)
  };

  // ---------- DOM helpers (XSS-safe; no innerHTML with user data) ----------
  MAF.el = function (tag, opts) {
    const e = document.createElement(tag);
    if (!opts) return e;
    if (opts.class) e.className = opts.class;
    if (opts.id) e.id = opts.id;
    if (opts.text != null) e.textContent = String(opts.text);
    if (opts.attrs) for (const k of Object.keys(opts.attrs)) e.setAttribute(k, opts.attrs[k]);
    if (opts.style) for (const k of Object.keys(opts.style)) e.style.setProperty(k, opts.style[k]);
    if (opts.children) for (const c of opts.children) if (c) e.appendChild(c);
    if (opts.onClick) e.addEventListener('click', opts.onClick);
    if (opts.onSubmit) e.addEventListener('submit', opts.onSubmit);
    if (opts.onInput) e.addEventListener('input', opts.onInput);
    return e;
  };

  MAF.escapeHtml = function (s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  MAF.clear = function (node) { while (node.firstChild) node.removeChild(node.firstChild); };

  // ---------- Fetch with basic-auth retry ----------
  MAF.fetch = async function (pathOrUrl, opts = {}) {
    const url = pathOrUrl.startsWith('/') ? pathOrUrl : MAF.api + '/' + pathOrUrl;
    const headers = Object.assign({ 'Accept': 'application/json' }, opts.headers || {});
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(opts.body);
    }
    if (MAF.state.creds) {
      headers['Authorization'] = 'Basic ' + btoa(MAF.state.creds.user + ':' + MAF.state.creds.pass);
    }
    const r = await fetch(url, Object.assign({}, opts, { headers, credentials: 'same-origin' }));
    if (r.status === 401 && !MAF.state.creds) {
      const u = prompt('Usuário Maffini Dashboard:');
      if (!u) throw new Error('auth cancelled');
      const p = prompt('Senha:');
      if (p == null) throw new Error('auth cancelled');
      MAF.state.creds = { user: u, pass: p };
      return MAF.fetch(pathOrUrl, opts);
    }
    if (!r.ok) {
      let detail = r.statusText;
      try { const j = await r.json(); if (j.error) detail = j.error; } catch (e) { void e; }
      throw new Error('HTTP ' + r.status + ': ' + detail);
    }
    if (r.status === 204) return null;
    const ct = r.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) return r.json();
    return r.text();
  };

  // ---------- Toast ----------
  MAF.toast = function (msg, kind) {
    const t = MAF.el('div', { class: 'toast' + (kind ? ' is-' + kind : ''), text: msg });
    document.body.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3000);
  };

  // ---------- Routing ----------
  MAF.routes = {};

  MAF.register = function (name, fn) { MAF.routes[name] = fn; };

  MAF.openView = async function (name) {
    if (!MAF.routes[name]) {
      MAF.openView('home');
      return;
    }
    MAF.state.currentView = name;
    document.querySelectorAll('.nav__item').forEach(b => {
      b.classList.toggle('is-active', b.dataset.view === name);
    });
    const wrap = document.querySelector('#view .view-wrap');
    MAF.clear(wrap);
    wrap.appendChild(MAF.el('p', { class: 'loading', text: 'Carregando ' + name + '…' }));
    try {
      const content = await MAF.routes[name]();
      MAF.clear(wrap);
      wrap.appendChild(content);
      const main = document.querySelector('#view');
      if (main) main.focus({ preventScroll: false });
    } catch (e) {
      MAF.clear(wrap);
      const box = MAF.el('div', { class: 'empty', children: [
        MAF.el('h2', { text: 'Erro ao carregar' }),
        MAF.el('p', { text: e.message })
      ]});
      wrap.appendChild(box);
    }
  };

  // ---------- Brand load + nav wiring ----------
  MAF.boot = async function () {
    try {
      const brand = await MAF.fetch('/api/brand');
      MAF.state.brand = brand.brand;
      MAF.state.areas = brand.areas || [];
      MAF.renderAreasNav();
    } catch (e) { console.warn('brand load failed', e); }

    document.querySelectorAll('.nav__item[data-view]').forEach(btn => {
      btn.addEventListener('click', () => MAF.openView(btn.dataset.view));
    });

    MAF.openView('home');
    MAF.refreshHealth();
    setInterval(MAF.refreshHealth, 60_000);
  };

  MAF.renderAreasNav = function () {
    const host = document.getElementById('areas-nav');
    if (!host) return;
    MAF.clear(host);
    for (const a of MAF.state.areas) {
      const b = MAF.el('button', { class: 'nav__area', attrs: { 'data-area': a.key } });
      const dot = MAF.el('span', { class: 'nav__area-dot' });
      dot.style.background = a.color;
      b.appendChild(dot);
      b.appendChild(MAF.el('span', { text: a.label }));
      b.addEventListener('click', () => {
        MAF.openView('prazos');
        setTimeout(() => { window.dispatchEvent(new CustomEvent('maf:area-filter', { detail: { key: a.key } })); }, 50);
      });
      host.appendChild(b);
    }
  };

  MAF.refreshHealth = async function () {
    const pulse = document.getElementById('health-pulse');
    if (!pulse) return;
    try {
      const h = await MAF.fetch('/api/health');
      const ok = h.legalops && h.legalops.status === 'healthy';
      pulse.classList.remove('is-loading', 'is-ok', 'is-degraded', 'is-down');
      pulse.classList.add(ok ? 'is-ok' : 'is-degraded');
      pulse.setAttribute('title', ok ? 'Sistema saudável' : 'Sistema com aviso');
    } catch (e) {
      pulse.classList.remove('is-loading', 'is-ok', 'is-degraded');
      pulse.classList.add('is-down');
      pulse.setAttribute('title', 'Sistema fora do ar: ' + e.message);
    }
  };

  // ---------- Date helpers ----------
  MAF.fmt = {
    dateBR: function (iso) {
      if (!iso) return '—';
      const d = typeof iso === 'string' ? new Date(iso) : iso;
      if (isNaN(d)) return '—';
      return d.toLocaleDateString('pt-BR');
    },
    dayMonth: function (iso) {
      if (!iso) return { d: '—', m: '' };
      const d = new Date(iso);
      if (isNaN(d)) return { d: '—', m: '' };
      const months = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
      return { d: String(d.getDate()).padStart(2, '0'), m: months[d.getMonth()] };
    },
    saudacao: function () {
      const h = new Date().getHours();
      if (h < 12) return 'Bom dia';
      if (h < 18) return 'Boa tarde';
      return 'Boa noite';
    }
  };

  // ---------- Approval modal (human-in-the-loop gate) ----------
  // Builds a modal from a command descriptor. NOTHING runs until the user
  // checks the review box AND clicks "Autorizo a execução".
  MAF.confirmCommand = function (cmd) {
    const backdrop = MAF.el('div', { class: 'modal-backdrop', attrs: { role: 'dialog', 'aria-modal': 'true', 'aria-label': cmd.label || 'Comando' } });
    const modal = MAF.el('div', { class: 'modal' });

    function close() {
      document.removeEventListener('keydown', onKey);
      backdrop.remove();
    }
    function onKey(e) { if (e.key === 'Escape') close(); }
    document.addEventListener('keydown', onKey);
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) close(); });

    // Header
    modal.appendChild(MAF.el('h2', { class: 'modal__title', text: cmd.label || cmd.id }));
    if (cmd.blurb) modal.appendChild(MAF.el('p', { class: 'modal__blurb', text: cmd.blurb }));

    // Danger banner
    const lvl = cmd.dangerLevel;
    if (lvl === 'high' || lvl === 'medium') {
      modal.appendChild(MAF.el('div', {
        class: 'modal__banner is-' + (lvl === 'high' ? 'urgent' : 'warning'),
        text: lvl === 'high'
          ? '⚠ Ação de alto impacto — revise com cuidado antes de autorizar.'
          : '⚠ Ação sensível — confirme os dados antes de prosseguir.'
      }));
    }

    // Dynamic form
    const form = MAF.el('form', { class: 'modal__form' });
    const controls = {};
    for (const inp of (cmd.inputs || [])) {
      const field = MAF.el('div', { class: 'field' });
      const labelText = (inp.label || inp.key) + (inp.required ? ' *' : '');
      field.appendChild(MAF.el('label', { text: labelText, attrs: { for: 'mc-' + inp.key } }));
      let ctl;
      const baseAttrs = { id: 'mc-' + inp.key, name: inp.key };
      if (inp.required) baseAttrs.required = 'true';
      switch (inp.type) {
        case 'textarea':
          ctl = MAF.el('textarea', { attrs: Object.assign(baseAttrs, inp.placeholder ? { placeholder: inp.placeholder } : {}) });
          break;
        case 'select':
          ctl = MAF.el('select', { attrs: baseAttrs });
          for (const opt of (inp.options || [])) {
            const o = typeof opt === 'object' ? opt : { value: opt, label: opt };
            ctl.appendChild(new Option(o.label, o.value));
          }
          break;
        case 'number':
          ctl = MAF.el('input', { attrs: Object.assign(baseAttrs, { type: 'number' }, inp.placeholder ? { placeholder: inp.placeholder } : {}) });
          break;
        case 'checkbox':
          ctl = MAF.el('input', { attrs: Object.assign(baseAttrs, { type: 'checkbox' }) });
          break;
        default:
          ctl = MAF.el('input', { attrs: Object.assign(baseAttrs, { type: 'text' }, inp.placeholder ? { placeholder: inp.placeholder } : {}) });
      }
      controls[inp.key] = { ctl, type: inp.type };
      field.appendChild(ctl);
      if (inp.redactable) {
        field.appendChild(MAF.el('small', { class: 'field__note', text: '🛡 PII será redigida antes de processar' }));
      }
      form.appendChild(field);
    }
    modal.appendChild(form);

    // Result host
    const resultBox = MAF.el('div', { class: 'modal__result' });
    modal.appendChild(resultBox);

    // Confirm gate
    const gateLabel = MAF.el('label', { class: 'modal__gate' });
    const gateBox = MAF.el('input', { attrs: { type: 'checkbox' } });
    gateLabel.appendChild(gateBox);
    gateLabel.appendChild(MAF.el('span', { text: 'Confirmo que revisei esta ação' }));
    modal.appendChild(gateLabel);

    // Buttons
    const actions = MAF.el('div', { class: 'modal__actions' });
    const cancelBtn = MAF.el('button', { class: 'btn btn--ghost', attrs: { type: 'button' }, text: 'Cancelar', onClick: close });
    const okBtn = MAF.el('button', { class: 'btn btn--gold', attrs: { type: 'button', disabled: 'true' }, text: 'Autorizo a execução' });
    gateBox.addEventListener('change', () => {
      if (gateBox.checked) okBtn.removeAttribute('disabled');
      else okBtn.setAttribute('disabled', 'true');
    });
    actions.appendChild(cancelBtn);
    actions.appendChild(okBtn);
    modal.appendChild(actions);

    function collectInputs() {
      const out = {};
      for (const name of Object.keys(controls)) {
        const { ctl, type } = controls[name];
        out[name] = type === 'checkbox' ? ctl.checked
          : type === 'number' ? (ctl.value === '' ? null : Number(ctl.value))
          : ctl.value;
      }
      return out;
    }

    okBtn.addEventListener('click', async () => {
      if (!gateBox.checked) return;
      // Required-field validation
      for (const inp of (cmd.inputs || [])) {
        if (inp.required && inp.type !== 'checkbox') {
          const v = controls[inp.key].ctl.value;
          if (!String(v || '').trim()) {
            controls[inp.key].ctl.classList.add('is-invalid');
            MAF.toast('Campo obrigatório: ' + (inp.label || inp.key), 'error');
            return;
          }
          controls[inp.key].ctl.classList.remove('is-invalid');
        }
      }
      okBtn.setAttribute('disabled', 'true');
      cancelBtn.setAttribute('disabled', 'true');
      MAF.clear(resultBox);
      resultBox.appendChild(MAF.el('p', { class: 'loading', text: 'Executando…' }));
      try {
        const res = await MAF.fetch('/api/command/run', {
          method: 'POST',
          body: { id: cmd.id, inputs: collectInputs(), approved: true }
        });
        MAF.clear(resultBox);
        resultBox.appendChild(MAF.el('div', { class: 'modal__banner is-ok', text: '✓ Comando executado.' }));
        resultBox.appendChild(MAF.el('pre', { class: 'modal__json', text: JSON.stringify(res, null, 2) }));
        MAF.toast('Comando executado', 'success');
        cancelBtn.removeAttribute('disabled');
        cancelBtn.textContent = 'Fechar';
      } catch (err) {
        MAF.clear(resultBox);
        const m = err.message || String(err);
        let note = 'Erro ao executar.';
        let kind = 'urgent';
        if (/HTTP 501/.test(m)) { note = 'Ainda não implementado (esperado em v0.1 para comandos internos/jurídicos).'; kind = 'warning'; }
        else if (/HTTP 403/.test(m)) { note = 'Autorização ausente — recarregue e tente de novo.'; }
        else if (/HTTP 400/.test(m)) { note = 'Dados inválidos — verifique os campos obrigatórios.'; }
        else if (/HTTP 500/.test(m)) { note = 'Erro interno no servidor.'; }
        resultBox.appendChild(MAF.el('div', { class: 'modal__banner is-' + kind, text: note }));
        resultBox.appendChild(MAF.el('pre', { class: 'modal__json', text: m }));
        MAF.toast(note, kind === 'warning' ? 'warning' : 'error');
        okBtn.removeAttribute('disabled');
        cancelBtn.removeAttribute('disabled');
      }
    });

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    (cmd.inputs && cmd.inputs.length ? form.querySelector('input,textarea,select') : gateBox).focus();
    return backdrop;
  };

  window.MAF = MAF;
})();
