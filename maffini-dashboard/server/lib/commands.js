'use strict';
// Commands registry — single source of truth.
//
// Each command:
//   id              : stable string id (used in API + audit)
//   label           : human label (pt-BR)
//   group           : cluster (operacoes | contratos | ma | lgpd | ingest |
//                              templates | notify | sistema | claude_legal)
//   areas           : array of Maffini practice areas (filter)
//   icon            : single char hint
//   blurb           : 1-line description shown in button + confirm dialog
//   inputs          : [{ key, label, type, required, placeholder, redactable }]
//   exec            : { kind: 'legalops'|'claude_legal'|'notify'|'internal',
//                       args: (input) => string[],   // for legalops
//                       skill: string,                // for claude_legal
//                       stdinKey: string,             // body field to stdin
//                       outputType: 'json'|'text' }
//   requiresApproval: boolean (default true)
//   dangerLevel     : 'low'|'medium'|'high' — UI shading + extra warning
//   audit           : { action: string, resource: string }
//
// LGPD: any `redactable: true` input is hashed before logging.

function asArray(v) { return Array.isArray(v) ? v : (v ? [v] : []); }

// JSON-list inputs may arrive already-serialized (textarea string) or as a
// parsed array/object (API client). Normalize to a JSON string for the CLI flag
// without double-encoding an existing JSON string.
function asJsonArg(v) {
  return typeof v === 'string' ? v : JSON.stringify(v);
}

const COMMANDS = [
  // ─────────────── operacoes ───────────────
  {
    id: 'intimacao_pipeline',
    label: 'Processar intimação',
    group: 'operacoes',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✉',
    blurb: 'Redige PII · identifica processo · calcula prazo CPC · grava audit',
    inputs: [
      { key: 'text', label: 'Texto do email/intimação', type: 'textarea', required: true, redactable: true },
      { key: 'parte', label: 'Parte', type: 'select',
        options: ['particular','fazenda','mp','defensoria'], default: 'particular' },
      { key: 'cliente_alias', label: 'Alias do cliente (não use nome real)', type: 'text', placeholder: 'CLI-021' },
      { key: 'sender', label: 'Sender (força detecção tribunal)', type: 'text', placeholder: 'x@tjpr.jus.br' },
      { key: 'persist', label: 'Salvar prazos resultantes', type: 'checkbox', default: true }
    ],
    exec: {
      kind: 'legalops',
      args: ({ parte, hoje, sender }) => {
        const a = ['pipeline', '--parte', parte || 'particular'];
        if (hoje) a.push('--hoje', hoje);
        if (sender) a.push('--sender', sender);
        return a;
      },
      stdinKey: 'text',
      outputType: 'json',
      // hint: route layer also persists prazos when input.persist === true
      postPersist: 'prazos'
    },
    audit: { action: 'intimacao_pipeline', resource: 'pipeline' }
  },
  {
    id: 'pii_redact',
    label: 'Redigir PII de um texto',
    group: 'operacoes',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '◐',
    blurb: 'Aplica redactor LGPD a um texto solto (sem persist)',
    inputs: [
      { key: 'text', label: 'Texto', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'legalops', args: () => ['redact', '--json'], stdinKey: 'text', outputType: 'json' },
    audit: { action: 'redact', resource: 'text' },
    dangerLevel: 'low'
  },
  {
    id: 'parse_intimacao',
    label: 'Parse intimação (sem pipeline)',
    group: 'operacoes',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '⟶',
    blurb: 'Só extrai processo + tipo + prazo (não calcula, não grava audit)',
    inputs: [{ key: 'text', label: 'Texto', type: 'textarea', required: true, redactable: true }],
    exec: { kind: 'legalops', args: () => ['parse'], stdinKey: 'text', outputType: 'json' },
    audit: { action: 'parse', resource: 'text' },
    dangerLevel: 'low'
  },
  {
    id: 'batch_eml_dir',
    label: 'Processar diretório de .eml',
    group: 'operacoes',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '☰',
    blurb: 'Roda pipeline em batch sobre todos .eml em um diretório',
    inputs: [
      { key: 'dir', label: 'Caminho do diretório', type: 'text', required: true, placeholder: '/var/lib/maffini/inbox' },
      { key: 'parte', label: 'Parte', type: 'select',
        options: ['particular','fazenda','mp','defensoria'], default: 'particular' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ dir, parte }) => ['batch', '--dir', dir, '--parte', parte || 'particular'],
      outputType: 'json'
    },
    audit: { action: 'batch', resource: 'directory' }
  },

  // ─────────────── contratos ───────────────
  {
    id: 'contract_analyze',
    label: 'Analisar contrato (CDC + abusividade)',
    group: 'contratos',
    areas: ['bancario', 'digital', 'preventivo'],
    icon: '§',
    blurb: 'Detecta cláusulas abusivas CDC + risco financiamento',
    inputs: [
      { key: 'text', label: 'Texto do contrato', type: 'textarea', required: true, redactable: true },
      { key: 'skip_redact', label: 'Pular redact (texto já redigido)', type: 'checkbox', default: false }
    ],
    exec: {
      kind: 'legalops',
      args: ({ skip_redact }) => skip_redact ? ['contract', '--skip-redact'] : ['contract'],
      stdinKey: 'text', outputType: 'json'
    },
    audit: { action: 'contract_analyze', resource: 'contract' }
  },
  {
    id: 'renewal_check',
    label: 'Verificar renovação de contrato',
    group: 'contratos',
    areas: ['bancario', 'preventivo'],
    icon: '⟳',
    blurb: 'Detecta cláusulas de renovação automática e prazo de denúncia (LegalOps v1.2)',
    inputs: [
      { key: 'text', label: 'Texto do contrato', type: 'textarea', required: true, redactable: true }
    ],
    // Note: there isn't a dedicated CLI subcmd for renewal — caller uses contract_analyze + custom parser.
    // Until renewal_watcher gets its own CLI, route this to contract_analyze with flag.
    exec: { kind: 'legalops', args: () => ['contract'], stdinKey: 'text', outputType: 'json' },
    audit: { action: 'renewal_check', resource: 'contract' }
  },

  // ─────────────── m&a / dd ───────────────
  {
    id: 'due_diligence_init',
    label: 'Iniciar Due Diligence (M&A)',
    group: 'ma',
    areas: ['bancario', 'preventivo'],
    icon: '⛯',
    blurb: 'Emite checklist padrão de due diligence BR, filtrável por área (v0.3)',
    inputs: [
      { key: 'area', label: 'Área (opcional — vazio = todas)', type: 'select',
        options: ['', 'trabalhista','fiscal','ambiental','contratual','societario'], default: '' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ area }) => {
        const a = ['due-diligence'];
        if (area) a.push('--area', area);
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'dd_init', resource: 'data_room' },
    dangerLevel: 'medium'
  },
  {
    id: 'red_flags_scan',
    label: 'Scan red flags em documento',
    group: 'ma',
    areas: ['bancario', 'preventivo'],
    icon: '⚑',
    blurb: 'Identifica red flags societários / financeiros (LegalOps v1.3)',
    inputs: [
      { key: 'text', label: 'Texto do documento', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'legalops', args: () => ['red-flags'], stdinKey: 'text', outputType: 'json' },
    audit: { action: 'red_flags_scan', resource: 'document' }
  },
  {
    id: 'disclosure_draft',
    label: 'Cross-check disclosure schedule',
    group: 'ma',
    areas: ['bancario', 'preventivo'],
    icon: '⟆',
    blurb: 'Cruza representações vs disclosure schedule — gaps + inconsistências (v0.3)',
    inputs: [
      { key: 'representacoes', label: 'Representações (JSON list de {id,texto,requer_schedule})', type: 'textarea',
        required: true, placeholder: '[{"id":"R-1","texto":"rep um","requer_schedule":true}]' },
      { key: 'schedule', label: 'Schedule (JSON list de {rep_id,conteudo}; opcional)', type: 'textarea',
        placeholder: '[{"rep_id":"R-1","conteudo":"..."}]' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ representacoes, schedule }) => {
        const a = ['disclosure', '--representacoes', asJsonArg(representacoes)];
        if (schedule !== undefined && schedule !== null && schedule !== '') {
          a.push('--schedule', asJsonArg(schedule));
        }
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'disclosure_draft', resource: 'data_room' }
  },
  {
    id: 'societario_review',
    label: 'Revisão societária (participações)',
    group: 'ma',
    areas: ['bancario', 'preventivo'],
    icon: '⚖',
    blurb: 'Valida coerência de participações societárias (CC/2002) — LegalOps v0.3',
    inputs: [
      { key: 'socios', label: 'Sócios (JSON list de {nome_alias,percentual,tipo}; alias only)', type: 'textarea',
        required: true, placeholder: '[{"nome_alias":"SOCIO-A","percentual":60,"tipo":"quotista"}]' },
      { key: 'tipo', label: 'Tipo societário', type: 'select',
        options: ['ltda','sa_fechada','sa_aberta','eireli','mei','slu','desconhecido'], default: 'ltda' },
      { key: 'cnpj', label: 'CNPJ (opcional)', type: 'text', placeholder: '00.000.000/0001-00' },
      { key: 'capital_social', label: 'Capital social (opcional)', type: 'number' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ socios, tipo, cnpj, capital_social }) => {
        const a = ['societario', '--socios', asJsonArg(socios)];
        if (tipo) a.push('--tipo', tipo);
        if (cnpj) a.push('--cnpj', cnpj);
        if (capital_social !== undefined && capital_social !== null && capital_social !== '') {
          a.push('--capital-social', String(capital_social));
        }
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'societario_review', resource: 'act' }
  },

  // ─────────────── lgpd ───────────────
  {
    id: 'dsar_process',
    label: 'Processar DSAR (Art. 18)',
    group: 'lgpd',
    areas: ['digital', 'medico', 'saude'],
    icon: '◷',
    blurb: 'Classifica direito invocado + calcula prazo Art. 19 (15 dias)',
    inputs: [
      { key: 'request_id', label: 'Request ID', type: 'text', required: true, placeholder: 'REQ-2026-001' },
      { key: 'titular_ref', label: 'Hash do titular (NÃO use nome real)', type: 'text', required: true, placeholder: 'hash:abc' },
      { key: 'text', label: 'Texto da requisição', type: 'textarea', required: true, redactable: true },
      { key: 'direito', label: 'Direito (Art. 18 código)', type: 'select',
        options: ['', '1','2','3','4','5','6','7','8','9'] }
    ],
    exec: {
      kind: 'legalops',
      args: ({ request_id, titular_ref, direito }) => {
        const a = ['dsar', '--request-id', request_id, '--titular-ref', titular_ref];
        if (direito) a.push('--direito', direito);
        return a;
      },
      stdinKey: 'text', outputType: 'json'
    },
    audit: { action: 'dsar_process', resource: 'dsar' }
  },
  {
    id: 'pia_ripd',
    label: 'Avaliar RIPD (PIA)',
    group: 'lgpd',
    areas: ['digital', 'medico', 'saude'],
    icon: '⊛',
    blurb: 'Avalia risco LGPD de uma operação (Privacy Impact Assessment)',
    inputs: [
      { key: 'tipo_operacao', label: 'Tipo de operação', type: 'text', required: true, placeholder: 'coleta' },
      { key: 'finalidade', label: 'Finalidade do tratamento', type: 'text', required: true },
      { key: 'base_legal', label: 'Base legal', type: 'select',
        options: ['legitimo_interesse','consentimento','obrigacao_legal','tutela_saude','execucao_contrato','exercicio_direito','protecao_vida','protecao_credito','pesquisa','politica_publica'],
        default: 'legitimo_interesse' },
      { key: 'tipos_dados', label: 'Tipos de dados', type: 'select',
        options: ['comum','sensivel','crianca'], default: 'comum' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ tipo_operacao, finalidade, base_legal, tipos_dados }) => {
        const a = ['pia', '--tipo-operacao', tipo_operacao, '--finalidade', finalidade,
          '--base-legal', base_legal || 'legitimo_interesse'];
        if (tipos_dados) a.push('--tipos-dados', tipos_dados);
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'pia_ripd', resource: 'operation' }
  },
  {
    id: 'dpa_template',
    label: 'Gerar DPA (Data Processing Agreement)',
    group: 'lgpd',
    areas: ['digital'],
    icon: '⊞',
    blurb: 'Template DPA preenchido (LegalOps v1.4)',
    inputs: [
      { key: 'controlador', label: 'Alias controlador', type: 'text', required: true },
      { key: 'operador', label: 'Alias operador', type: 'text', required: true },
      { key: 'finalidade', label: 'Finalidade tratamento', type: 'text', required: true },
      { key: 'objeto', label: 'Objeto do acordo', type: 'text' },
      { key: 'categorias', label: 'Categorias de dados (vírgula)', type: 'text', placeholder: 'nome,email' },
      { key: 'prazo_retencao', label: 'Prazo de retenção', type: 'text' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ controlador, operador, finalidade, objeto, categorias, prazo_retencao }) => {
        const a = ['dpa', '--controlador', controlador, '--operador', operador,
          '--finalidade', finalidade];
        if (objeto) a.push('--objeto', objeto);
        if (categorias) a.push('--categorias', categorias);
        if (prazo_retencao) a.push('--prazo-retencao', prazo_retencao);
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'dpa_template', resource: 'agreement' }
  },
  {
    id: 'anpd_playbook',
    label: 'Playbook ANPD (incidente)',
    group: 'lgpd',
    areas: ['digital', 'medico', 'saude'],
    icon: '⚠',
    blurb: 'Roteiro de notificação ANPD em 24h (LGPD Art. 48)',
    inputs: [
      { key: 'tipo_incidente', label: 'Tipo', type: 'select',
        options: ['vazamento','acesso_indevido','perda','outro'], default: 'vazamento' },
      { key: 'descricao', label: 'Descrição', type: 'textarea', required: true, redactable: true },
      { key: 'dados_afetados', label: 'Dados afetados', type: 'select',
        options: ['comum','sensivel','crianca'], default: 'comum' },
      { key: 'num_titulares', label: 'Nº titulares afetados', type: 'number', default: 0 }
    ],
    exec: {
      kind: 'legalops',
      // descricao goes as a flag (CLI redige PII internamente); tipo_incidente=vazamento
      // sets --vazamento-confirmado (deterministic mapping).
      args: ({ descricao, tipo_incidente, dados_afetados, num_titulares }) => {
        const a = ['anpd', '--descricao', descricao,
          '--num-titulares', String(num_titulares || 0)];
        if (dados_afetados) a.push('--dados-afetados', dados_afetados);
        if (tipo_incidente === 'vazamento') a.push('--vazamento-confirmado');
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'anpd_playbook', resource: 'incident' },
    dangerLevel: 'high'
  },
  {
    id: 'vendor_ai_review',
    label: 'Revisar fornecedor de IA',
    group: 'lgpd',
    areas: ['digital'],
    icon: '⊠',
    blurb: 'Emite checklist LGPD/ANPD padrão para fornecedor de IA (v0.3)',
    inputs: [],
    exec: {
      kind: 'legalops',
      args: () => ['vendor-review', '--format', 'json'],
      outputType: 'json'
    },
    audit: { action: 'vendor_ai_review', resource: 'vendor' }
  },

  // ─────────────── ingest ───────────────
  {
    id: 'm365_fetch',
    label: 'Buscar intimações no Outlook (últimos N dias)',
    group: 'ingest',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '⤓',
    blurb: 'M365 Graph API · `from` filter · fetch recentes (LegalOps m365_ingest)',
    inputs: [
      { key: 'days', label: 'Dias', type: 'number', default: 7 },
      { key: 'sender_filter', label: 'Filtrar sender (opc)', type: 'text', placeholder: 'tjpr.jus.br' }
    ],
    exec: { kind: 'internal', module: 'm365_ingest', op: 'fetch_recent' },
    audit: { action: 'm365_fetch', resource: 'outlook' },
    requiresApproval: true,
    dangerLevel: 'medium'
  },
  {
    id: 'bacen_cvm_check',
    label: 'Verificar atualizações BACEN/CVM',
    group: 'ingest',
    areas: ['bancario'],
    icon: '⤒',
    blurb: 'Lê feeds BACEN/CVM e marca itens novos relevantes (LegalOps)',
    inputs: [],
    exec: { kind: 'internal', module: 'bacen_cvm_feeds', op: 'check' },
    audit: { action: 'bacen_cvm_check', resource: 'feeds' }
  },
  {
    id: 'tribunal_detect',
    label: 'Detectar tribunal de um email',
    group: 'ingest',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '◇',
    blurb: 'Identifica tribunal por sender + assinatura no corpo',
    inputs: [
      { key: 'text', label: 'Texto', type: 'textarea', required: true, redactable: true },
      { key: 'sender', label: 'Sender', type: 'text' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ sender }) => {
        const a = ['tribunal-detect'];
        if (sender) a.push('--sender', sender);
        return a;
      },
      stdinKey: 'text', outputType: 'json'
    },
    audit: { action: 'tribunal_detect', resource: 'text' },
    dangerLevel: 'low'
  },

  // ─────────────── templates ───────────────
  {
    id: 'doc_template_render',
    label: 'Renderizar template (procuração/petição)',
    group: 'templates',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '📄',
    blurb: 'Preenche template com variáveis ({cliente_alias} etc)',
    inputs: [
      { key: 'template_id', label: 'Template', type: 'select',
        options: ['procuracao','contrato_honorarios'],
        required: true },
      { key: 'vars', label: 'Variáveis (JSON)', type: 'textarea',
        placeholder: '{"outorgante":"CLI-021","outorgado":"ADV-002","comarca":"Curitiba"}' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ template_id, vars }) => ['doc-template', '--template', template_id, '--vars', vars || '{}'],
      outputType: 'json'
    },
    audit: { action: 'doc_template_render', resource: 'template' }
  },
  {
    id: 'doc_extract',
    label: 'Extrair texto de documento (.eml/.txt)',
    group: 'templates',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '⌹',
    blurb: 'Doc extractor LegalOps v1.1',
    inputs: [
      { key: 'path', label: 'Caminho', type: 'text', required: true },
      { key: 'kind', label: 'Tipo de documento', type: 'select',
        options: ['procuracao','contrato_honorarios'], default: 'procuracao' }
    ],
    exec: {
      kind: 'legalops',
      args: ({ path, kind }) => ['doc-extract', '--input', path, '--kind', kind || 'procuracao'],
      outputType: 'json'
    },
    audit: { action: 'doc_extract', resource: 'document' }
  },

  // ─────────────── notify ───────────────
  {
    id: 'notify_whatsapp',
    label: 'Enviar resumo prazos via WhatsApp',
    group: 'notify',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✎',
    blurb: 'Pipeline + envia urgentes via bridge :3000',
    inputs: [
      { key: 'chat_id', label: 'Chat ID', type: 'text', required: true, placeholder: '554199...@s.whatsapp.net' },
      { key: 'dry_run', label: 'Dry-run (não envia, só formata)', type: 'checkbox', default: true }
    ],
    exec: {
      kind: 'legalops',
      args: ({ chat_id, dry_run }) => {
        const a = ['notify', '--chat-id', chat_id, '--channels', 'whatsapp'];
        if (dry_run) a.push('--dry-run');
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'notify_whatsapp', resource: 'notification' },
    dangerLevel: 'high'
  },
  {
    id: 'notify_email',
    label: 'Enviar resumo prazos por email',
    group: 'notify',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✉',
    blurb: 'SMTP configurado em config.toml',
    inputs: [
      { key: 'dry_run', label: 'Dry-run', type: 'checkbox', default: true }
    ],
    exec: {
      kind: 'legalops',
      args: ({ dry_run }) => {
        const a = ['notify', '--channels', 'email'];
        if (dry_run) a.push('--dry-run');
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'notify_email', resource: 'notification' },
    dangerLevel: 'high'
  },
  {
    id: 'notify_slack',
    label: 'Enviar resumo prazos no Slack',
    group: 'notify',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '#',
    blurb: 'Webhook configurado em config.toml',
    inputs: [
      { key: 'dry_run', label: 'Dry-run', type: 'checkbox', default: true }
    ],
    exec: {
      kind: 'legalops',
      args: ({ dry_run }) => {
        const a = ['notify', '--channels', 'slack'];
        if (dry_run) a.push('--dry-run');
        return a;
      },
      outputType: 'json'
    },
    audit: { action: 'notify_slack', resource: 'notification' },
    dangerLevel: 'high'
  },

  // ─────────────── sistema ───────────────
  {
    id: 'health',
    label: 'Verificar saúde do sistema',
    group: 'sistema',
    areas: [],
    icon: '◉',
    blurb: 'Health check de PII redactor + prazos + tribunal detector',
    inputs: [],
    exec: { kind: 'legalops', args: () => ['health', '--format', 'json'], outputType: 'json' },
    audit: { action: 'health', resource: 'system' },
    requiresApproval: false,
    dangerLevel: 'low'
  },
  {
    id: 'metrics_render',
    label: 'Renderizar métricas Prometheus',
    group: 'sistema',
    areas: [],
    icon: '☷',
    blurb: 'Pipeline sintético + render Prometheus exposition',
    inputs: [],
    exec: { kind: 'legalops', args: () => ['metrics'], outputType: 'text' },
    audit: { action: 'metrics', resource: 'system' },
    requiresApproval: false,
    dangerLevel: 'low'
  },
  {
    id: 'audit_verify',
    label: 'Verificar integridade do audit chain',
    group: 'sistema',
    areas: [],
    icon: '⛓',
    blurb: 'Recalcula chain HMAC-SHA256 e valida',
    inputs: [],
    exec: { kind: 'legalops', args: ({ db }) => ['audit', 'verify', '--db', db || '__AUDIT_DB__'], outputType: 'json' },
    audit: { action: 'audit_verify', resource: 'chain' },
    requiresApproval: false
  },
  {
    id: 'audit_list',
    label: 'Listar entradas do audit chain',
    group: 'sistema',
    areas: [],
    icon: '☰',
    blurb: 'Dump cronológico do audit log',
    inputs: [],
    exec: { kind: 'legalops', args: ({ db }) => ['audit', 'list', '--db', db || '__AUDIT_DB__'], outputType: 'json' },
    audit: { action: 'audit_list', resource: 'chain' },
    requiresApproval: false
  },

  // ─────────────── claude for legal (Anthropic) ───────────────
  {
    id: 'cfl_review_contract',
    label: 'Claude: revisar contrato (cláusulas + risco)',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:review-contract` — análise estruturada com LLM',
    inputs: [
      { key: 'text', label: 'Texto do contrato', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'claude_legal', skill: 'review-contract', stdinKey: 'text' },
    audit: { action: 'cfl_review_contract', resource: 'contract' },
    dangerLevel: 'medium'
  },
  {
    id: 'cfl_triage_nda',
    label: 'Claude: triagem de NDA',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:triage-nda` — classifica risco + recomenda assinatura',
    inputs: [
      { key: 'text', label: 'Texto da NDA', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'claude_legal', skill: 'triage-nda', stdinKey: 'text' },
    audit: { action: 'cfl_triage_nda', resource: 'nda' }
  },
  {
    id: 'cfl_compliance_check',
    label: 'Claude: compliance check',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:compliance-check`',
    inputs: [
      { key: 'context', label: 'Contexto / regulamento', type: 'textarea', required: true }
    ],
    exec: { kind: 'claude_legal', skill: 'compliance-check', stdinKey: 'context' },
    audit: { action: 'cfl_compliance_check', resource: 'compliance' }
  },
  {
    id: 'cfl_legal_risk',
    label: 'Claude: avaliação de risco jurídico',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:legal-risk-assessment`',
    inputs: [
      { key: 'context', label: 'Situação a avaliar', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'claude_legal', skill: 'legal-risk-assessment', stdinKey: 'context' },
    audit: { action: 'cfl_legal_risk', resource: 'risk' }
  },
  {
    id: 'cfl_vendor_check',
    label: 'Claude: vendor due diligence rápida',
    group: 'claude_legal',
    areas: ['bancario', 'digital'],
    icon: '✦',
    blurb: 'Skill `legal:vendor-check`',
    inputs: [
      { key: 'vendor', label: 'Nome do fornecedor', type: 'text', required: true },
      { key: 'context', label: 'Contexto contratação', type: 'textarea' }
    ],
    exec: { kind: 'claude_legal', skill: 'vendor-check', stdinKey: 'context' },
    audit: { action: 'cfl_vendor_check', resource: 'vendor' }
  },
  {
    id: 'cfl_brief',
    label: 'Claude: gerar memorial / brief',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:brief`',
    inputs: [
      { key: 'context', label: 'Briefing do caso', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'claude_legal', skill: 'brief', stdinKey: 'context' },
    audit: { action: 'cfl_brief', resource: 'brief' }
  },
  {
    id: 'cfl_legal_response',
    label: 'Claude: minutar resposta jurídica',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:legal-response`',
    inputs: [
      { key: 'context', label: 'Pedido / situação', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'claude_legal', skill: 'legal-response', stdinKey: 'context' },
    audit: { action: 'cfl_legal_response', resource: 'response' },
    dangerLevel: 'medium'
  },
  {
    id: 'cfl_meeting_briefing',
    label: 'Claude: briefing pré-reunião',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:meeting-briefing`',
    inputs: [
      { key: 'context', label: 'Pauta / participantes / contexto', type: 'textarea', required: true }
    ],
    exec: { kind: 'claude_legal', skill: 'meeting-briefing', stdinKey: 'context' },
    audit: { action: 'cfl_meeting_briefing', resource: 'meeting' }
  },
  {
    id: 'cfl_signature_request',
    label: 'Claude: preparar pedido de assinatura',
    group: 'claude_legal',
    areas: ['bancario', 'digital', 'medico', 'saude', 'preventivo'],
    icon: '✦',
    blurb: 'Skill `legal:signature-request`',
    inputs: [
      { key: 'context', label: 'Detalhes do documento', type: 'textarea', required: true, redactable: true }
    ],
    exec: { kind: 'claude_legal', skill: 'signature-request', stdinKey: 'context' },
    audit: { action: 'cfl_signature_request', resource: 'signature' },
    dangerLevel: 'medium'
  }
];

const GROUPS = [
  { key: 'operacoes',     label: 'Operações urgentes', order: 1 },
  { key: 'contratos',     label: 'Contratos & Renovações', order: 2 },
  { key: 'ma',            label: 'M&A / Due Diligence', order: 3 },
  { key: 'lgpd',          label: 'LGPD Assistant', order: 4 },
  { key: 'ingest',        label: 'Ingest & Detect', order: 5 },
  { key: 'templates',     label: 'Templates & Docs', order: 6 },
  { key: 'notify',        label: 'Notificações', order: 7 },
  { key: 'sistema',       label: 'Sistema & Auditoria', order: 8 },
  { key: 'claude_legal',  label: 'Claude for Legal (LLM)', order: 9 }
];

// Public catalog — strip exec internals for client (client only needs label+inputs+id).
function catalog() {
  return COMMANDS.map(c => ({
    id: c.id,
    label: c.label,
    group: c.group,
    areas: asArray(c.areas),
    icon: c.icon || '·',
    blurb: c.blurb || '',
    inputs: (c.inputs || []).map(i => ({
      key: i.key,
      label: i.label,
      type: i.type,
      required: !!i.required,
      placeholder: i.placeholder,
      options: i.options,
      default: i.default,
      redactable: !!i.redactable
    })),
    requiresApproval: c.requiresApproval !== false,
    dangerLevel: c.dangerLevel || 'low'
  }));
}

function getById(id) {
  return COMMANDS.find(c => c.id === id) || null;
}

module.exports = { COMMANDS, GROUPS, catalog, getById };
