const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "LegalOps BR — Automação Jurídica com IA";
pres.author = "Enzo Bromano";

const C = {
  navy: "1E2761",
  iceBlue: "CADCFC",
  white: "FFFFFF",
  lightBg: "F4F6FB",
  accent: "4A90D9",
  accentDark: "2C5FAD",
  gray: "64748B",
  dark: "1A1A2E",
  green: "16A34A",
  red: "DC2626",
  amber: "D97706",
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 2, angle: 135, color: "000000", opacity: 0.12 });

// ── SLIDE 1: Capa ───────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.35, h: 5.625, fill: { color: C.accent }, line: { color: C.accent } });
  s.addShape(pres.shapes.OVAL, { x: 8.2, y: -0.8, w: 2.8, h: 2.8, fill: { color: C.accentDark, transparency: 60 }, line: { color: C.accentDark, transparency: 60 } });
  s.addShape(pres.shapes.OVAL, { x: 8.8, y: -0.2, w: 1.8, h: 1.8, fill: { color: C.accent, transparency: 50 }, line: { color: C.accent, transparency: 50 } });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.1, w: 2.1, h: 0.32, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("PILOTO 2026", { x: 0.7, y: 1.1, w: 2.1, h: 0.32, fontSize: 10, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });

  s.addText("LegalOps BR", { x: 0.7, y: 1.6, w: 8.8, h: 1.1, fontSize: 52, bold: true, color: C.white, fontFace: "Calibri" });
  s.addText("Automação Jurídica com Inteligência Artificial", { x: 0.7, y: 2.65, w: 8.8, h: 0.6, fontSize: 22, color: C.iceBlue, fontFace: "Calibri" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 3.4, w: 5.0, h: 0.04, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("Proposta técnica para implementação de IA no escritório jurídico", { x: 0.7, y: 3.6, w: 8.5, h: 0.5, fontSize: 14, color: C.iceBlue, fontFace: "Calibri", italic: true });
  s.addText("Escritório Parceiro  ·  Maio 2026  ·  Confidencial", { x: 0.7, y: 5.1, w: 8.5, h: 0.35, fontSize: 11, color: "8899BB", fontFace: "Calibri" });
}

// ── SLIDE 2: O Problema ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("O Problema", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });
  s.addText("O dia a dia de um escritório jurídico consome horas em tarefas repetitivas", { x: 0.5, y: 1.0, w: 9, h: 0.4, fontSize: 15, color: C.gray, fontFace: "Calibri", italic: true });

  const problems = [
    { icon: "⏰", title: "Prazos manuais", desc: "Monitorar diariamente o Diário Oficial do TJPR, copiar dados, calcular prazos no CPC — trabalho manual, sujeito a erro humano." },
    { icon: "📄", title: "Documentos repetitivos", desc: "Procurações, contratos de serviço e peças processuais seguem estruturas fixas mas exigem horas de digitação e revisão." },
    { icon: "🔍", title: "Pesquisa jurisprudencial", desc: "Buscar precedentes relevantes em múltiplos tribunais consome tempo que poderia ser dedicado à estratégia do caso." },
  ];

  problems.forEach((p, i) => {
    const x = 0.35 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.55, w: 2.9, h: 3.5, fill: { color: C.white }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.55, w: 2.9, h: 0.06, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(p.icon, { x, y: 1.7, w: 2.9, h: 0.7, fontSize: 30, align: "center" });
    s.addText(p.title, { x: x + 0.15, y: 2.5, w: 2.6, h: 0.45, fontSize: 14, bold: true, color: C.dark, fontFace: "Calibri", align: "center" });
    s.addText(p.desc, { x: x + 0.15, y: 3.05, w: 2.6, h: 1.85, fontSize: 11.5, color: C.gray, fontFace: "Calibri", align: "left" });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 5.1, w: 9.3, h: 0.35, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Estima-se que 30–40% do tempo de advogados em escritórios de pequeno porte vai para tarefas que a IA pode automatizar.", {
    x: 0.35, y: 5.1, w: 9.3, h: 0.35, fontSize: 10.5, color: C.iceBlue, fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
  });
}

// ── SLIDE 3: A Solução ──────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("A Solução — LegalOps BR", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 1.0, w: 4.3, h: 4.35, fill: { color: C.lightBg }, line: { color: "D1D5DB" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 1.0, w: 4.3, h: 0.4, fill: { color: C.green }, line: { color: C.green } });
  s.addText("✅  O que É", { x: 0.35, y: 1.0, w: 4.3, h: 0.4, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: [0, 0, 0, 8] });

  const isItems = [
    "Plugin de IA integrado ao Claude Code (Anthropic)",
    "Assistente especializado em direito brasileiro",
    "Funciona no desktop existente — sem hardware novo",
    "Event-driven: age quando há novidade (prazo, peça)",
    "Open-source (Apache 2.0) com extensões BR customizadas",
    "Gate humano em toda ação concreta — a advogada decide sempre",
  ];
  s.addText(isItems.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < isItems.length - 1 } })), {
    x: 0.5, y: 1.5, w: 3.95, h: 3.7, fontSize: 11.5, color: C.dark, fontFace: "Calibri", paraSpaceAfter: 6,
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 5.0, y: 1.0, w: 4.65, h: 4.35, fill: { color: C.lightBg }, line: { color: "D1D5DB" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.0, y: 1.0, w: 4.65, h: 0.4, fill: { color: C.red }, line: { color: C.red } });
  s.addText("🚫  O que NÃO É", { x: 5.0, y: 1.0, w: 4.65, h: 0.4, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: [0, 0, 0, 8] });

  const notItems = [
    "Não é robô autônomo — não age sem aprovação humana",
    "Não substitui a advogada nem gera peças sem revisão",
    "Não é SaaS com mensalidade nem contrato longo",
    "Não armazena documentos brutos na nuvem",
    "Não envia CPF, RG, nome de cliente ao modelo de IA",
    "Não é chatbot genérico — especializado no escritório",
  ];
  s.addText(notItems.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < notItems.length - 1 } })), {
    x: 5.15, y: 1.5, w: 4.35, h: 3.7, fontSize: 11.5, color: C.dark, fontFace: "Calibri", paraSpaceAfter: 6,
  });
}

// ── SLIDE 4: DESTAQUE — M&A + Due Diligence ─────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: "0D1B2A" };

  // Accent left bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.35, h: 5.625, fill: { color: C.accent }, line: { color: C.accent } });

  // Decorative circles
  s.addShape(pres.shapes.OVAL, { x: 7.5, y: -1.0, w: 4.0, h: 4.0, fill: { color: "1C3550", transparency: 30 }, line: { color: "1C3550", transparency: 30 } });
  s.addShape(pres.shapes.OVAL, { x: 8.5, y: 3.5,  w: 2.5, h: 2.5, fill: { color: "1C3550", transparency: 40 }, line: { color: "1C3550", transparency: 40 } });

  // Badge
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.55, w: 3.5, h: 0.32, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("FUNCIONALIDADE ESTRATÉGICA · PRIORIDADE ALTA", { x: 0.7, y: 0.55, w: 3.5, h: 0.32, fontSize: 9, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });

  // Title
  s.addText("M&A + Due Diligence", { x: 0.7, y: 0.98, w: 8.5, h: 0.95, fontSize: 46, bold: true, color: C.white, fontFace: "Calibri" });
  s.addText("Nativo no Claude for Legal · Pronto para usar no piloto", { x: 0.7, y: 1.93, w: 7.5, h: 0.42, fontSize: 16, color: C.iceBlue, fontFace: "Calibri", italic: true });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 2.45, w: 6.5, h: 0.04, fill: { color: C.accent }, line: { color: C.accent } });

  // 3 capability cards
  const caps = [
    {
      icon: "🏢", title: "Fusões & Aquisições",
      items: ["Análise de estrutura societária", "Avaliação de quórum e cotas", "Identificação de riscos contratuais", "Mapeamento de passivos ocultos"],
    },
    {
      icon: "🔍", title: "Due Diligence",
      items: ["Checklist CVM / Junta / Receita", "Revisão de contratos em bloco", "Análise de pendências fiscais/trabalhistas", "Relatório consolidado de riscos"],
    },
    {
      icon: "📋", title: "Vantagem Claude for Legal",
      items: ["Treinado em direito corporativo BR", "Processa contratos longos sem perder contexto", "Geração de relatórios estruturados", "Integração com templates do escritório"],
    },
  ];

  caps.forEach((c, i) => {
    const x = 0.55 + i * 3.1;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.6, w: 2.95, h: 2.75, fill: { color: "1A2E45" }, line: { color: C.accent, width: 1 } });
    s.addText(c.icon, { x, y: 2.68, w: 2.95, h: 0.5, fontSize: 22, align: "center" });
    s.addText(c.title, { x: x + 0.1, y: 3.22, w: 2.75, h: 0.38, fontSize: 12.5, bold: true, color: C.iceBlue, fontFace: "Calibri", align: "center" });
    s.addText(c.items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < c.items.length - 1 } })), {
      x: x + 0.12, y: 3.65, w: 2.71, h: 1.6, fontSize: 10.5, color: "AAC4E0", fontFace: "Calibri", paraSpaceAfter: 4,
    });
  });

  // Bottom note
  s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: 5.12, w: 9.1, h: 0.36, fill: { color: C.accent, transparency: 80 }, line: { color: C.accent, transparency: 50 } });
  s.addText("⭐  M&A e Due Diligence são capacidades nativas do Claude for Legal (Apache 2.0) — sem custo adicional de licença, disponíveis a partir da fase v1.2.", {
    x: 0.65, y: 5.12, w: 8.9, h: 0.36, fontSize: 10, color: C.iceBlue, fontFace: "Calibri", valign: "middle",
  });
}

// ── SLIDE 5: Arquitetura 4 Anéis ────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Arquitetura — Os 4 Anéis de Proteção", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  // Concentric rings
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.95, w: 9.4, h: 4.5, fill: { color: "E0E7FF" }, line: { color: "93C5FD", width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.15, w: 8.8, h: 4.1, fill: { color: "DBEAFE" }, line: { color: "60A5FA", width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.9, y: 1.35, w: 8.2, h: 3.7, fill: { color: "BFDBFE" }, line: { color: "3B82F6", width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 1.2, y: 1.55, w: 7.6, h: 3.3, fill: { color: C.accentDark }, line: { color: C.navy, width: 1.5 } });

  // Center AI box
  s.addShape(pres.shapes.RECTANGLE, { x: 3.5, y: 2.3, w: 3.0, h: 1.6, fill: { color: C.navy }, line: { color: C.navy }, shadow: makeShadow() });
  s.addText("🤖", { x: 3.5, y: 2.35, w: 3.0, h: 0.55, fontSize: 26, align: "center" });
  s.addText("Claude AI\n(Anthropic)", { x: 3.5, y: 2.85, w: 3.0, h: 0.9, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle" });

  // Ring labels top-left
  s.addText("Anel 1 · Físico", { x: 1.25, y: 1.57, w: 2.0, h: 0.18, fontSize: 8.5, bold: true, color: C.white, fontFace: "Calibri" });
  s.addText("Anel 2 · Software", { x: 0.95, y: 1.37, w: 2.0, h: 0.18, fontSize: 8.5, bold: true, color: C.dark, fontFace: "Calibri" });
  s.addText("Anel 3 · Segurança", { x: 0.65, y: 1.17, w: 2.0, h: 0.18, fontSize: 8.5, bold: true, color: C.dark, fontFace: "Calibri" });
  s.addText("Anel 4 · Dados Sensíveis", { x: 0.35, y: 0.97, w: 2.3, h: 0.18, fontSize: 8.5, bold: true, color: C.dark, fontFace: "Calibri" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.1, w: 10, h: 0.525, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Cada anel é uma camada de proteção independente — se um falhar, os outros continuam protegendo os dados do cliente.", {
    x: 0.4, y: 5.1, w: 9.2, h: 0.525, fontSize: 11, color: C.iceBlue, fontFace: "Calibri", valign: "middle",
  });
}

// ── SLIDE 5: Fluxos de Automação ────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Fluxos de Automação — Por Fase", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  const phases = [
    { phase: "v0.1", label: "PoC Local", time: "Sem. 1–2", color: "16A34A", items: ["Sem dados reais", "Testa redação de peças com dados fictícios", "Valida cálculo de prazo CPC", "Testa fluxo completo sem risco"] },
    { phase: "v1.0", label: "TJPR Shadow", time: "Mês 1–2", color: "2563EB", items: ["Lê Diário Oficial do TJPR diariamente", "Identifica intimações do escritório", "Calcula prazos automaticamente", "Tia May confirma antes de qualquer ação"] },
    { phase: "v1.1", label: "Documentos", time: "Mês 3", color: "7C3AED", items: ["Rascunha procurações com dados do cliente", "Gera contratos de serviço estruturados", "Adapta templates do escritório", "Revisão humana sempre obrigatória"] },
    { phase: "v1.2+", label: "Expansão", time: "Mês 4–6+", color: C.amber, items: ["Contract AI — análise de contratos", "Pesquisa jurisprudencial assistida", "M&A e Due Diligence", "LGPD assistant"] },
  ];

  phases.forEach((p, i) => {
    const x = 0.25 + i * 2.38;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 2.2, h: 4.45, fill: { color: C.lightBg }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 2.2, h: 0.5, fill: { color: p.color }, line: { color: p.color } });
    s.addText(p.phase, { x, y: 0.95, w: 1.1, h: 0.5, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", align: "center", margin: 0 });
    s.addText(p.time, { x: x + 1.1, y: 0.95, w: 1.1, h: 0.5, fontSize: 10, color: "CCDDFF", fontFace: "Calibri", valign: "middle", align: "center", margin: 0, italic: true });
    s.addText(p.label, { x: x + 0.1, y: 1.52, w: 2.0, h: 0.38, fontSize: 12.5, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(p.items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < p.items.length - 1 } })), {
      x: x + 0.1, y: 1.95, w: 2.05, h: 3.3, fontSize: 10.5, color: C.gray, fontFace: "Calibri", paraSpaceAfter: 5,
    });
  });
}

// ── SLIDE 6: Segurança & LGPD ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Segurança & LGPD — Os 3 Medos Endereçados", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 24, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  const fears = [
    {
      icon: "🔒", title: "Privacidade & Sigilo",
      medo: "Dados de clientes saindo do escritório?",
      resp: ["PII-redactor mascara CPF, CNPJ, RG, nomes antes de qualquer chamada à IA", "Documentos brutos nunca saem do desktop — só fragmentos redacted", "Alinhado ao EOAB art. 34, XVI (sigilo profissional)", "LGPD: DPA assinado com Anthropic"],
    },
    {
      icon: "⚠️", title: "Falhas Irreversíveis",
      medo: "E se a IA cometer um erro grave?",
      resp: ["Gate humano em toda ação concreta — a advogada aprova antes de qualquer envio", "IA só sugere; Tia May decide e assina", "4 níveis de reversibilidade: cancelar → reprocessar → rollback → modo manual", "Shadow mode: IA monitora mas não age sem liberação"],
    },
    {
      icon: "💰", title: "Custo de Tokens",
      medo: "Risco de cobrança exorbitante?",
      resp: ["Stack de 3 tiers: Haiku (triagem) → Sonnet (rascunho) → Opus (crítico)", "Custo estimado: R$ 30–50/mês para volume do escritório", "Alerta automático ao atingir 70% do crédito mensal", "Hard stop: sistema pausa e aguarda instrução humana"],
    },
  ];

  fears.forEach((f, i) => {
    const x = 0.3 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 2.95, h: 4.45, fill: { color: C.white }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 2.95, h: 0.04, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(f.icon, { x, y: 1.05, w: 2.95, h: 0.6, fontSize: 28, align: "center" });
    s.addText(f.title, { x: x + 0.1, y: 1.7, w: 2.75, h: 0.5, fontSize: 12.5, bold: true, color: C.dark, fontFace: "Calibri", align: "center" });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.1, y: 2.25, w: 2.75, h: 0.38, fill: { color: "FEF2F2" }, line: { color: "FECACA" } });
    s.addText(f.medo, { x: x + 0.1, y: 2.25, w: 2.75, h: 0.38, fontSize: 10, italic: true, color: C.red, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
    s.addText(f.resp.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < f.resp.length - 1 } })), {
      x: x + 0.1, y: 2.7, w: 2.75, h: 2.55, fontSize: 10.5, color: C.gray, fontFace: "Calibri", paraSpaceAfter: 6,
    });
  });
}

// ── SLIDE 7: Dados — 3 Zonas ─────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Dados — 3 Zonas de Armazenamento", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  const zones = [
    {
      num: "1", title: "Servidores Anthropic", color: C.amber, bg: "FFFBEB",
      items: ["✅  Prompts redacted da Tia May", "✅  Fragmentos sem PII real", "🚫  Documentos brutos — bloqueado", "🚫  CPF / CNPJ / nomes reais", "🚫  Conteúdo bruto de emails TJPR"],
      note: "Retenção máx. 30 dias · DPA disponível",
    },
    {
      num: "2", title: "Desktop do Escritório", color: C.green, bg: "F0FDF4",
      items: ["✅  Documentos brutos originais", "✅  Audit log de todas as ações", "✅  Backups criptografados (BitLocker)", "✅  Templates e modelos do escritório", "✅  Histórico de clientes e processos"],
      note: "Dados sensíveis nunca saem desta zona",
    },
    {
      num: "3", title: "O que o Modelo Vê", color: C.accent, bg: "EFF6FF",
      items: ["✅  Texto redacted: '[CLIENTE_1] protocolou...'", "✅  Prazos e datas sem identificadores", "✅  Estrutura de peças sem conteúdo privado", "🚫  Nunca vê o documento original", "🚫  Nunca vê dados identificáveis"],
      note: "Princípio: mínima exposição de dados",
    },
  ];

  zones.forEach((z, i) => {
    const x = 0.25 + i * 3.2;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 3.0, h: 4.5, fill: { color: z.bg }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 3.0, h: 0.5, fill: { color: z.color }, line: { color: z.color } });
    s.addText(`Zona ${z.num}`, { x, y: 0.95, w: 0.7, h: 0.5, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", align: "center", margin: 0 });
    s.addText(z.title, { x: x + 0.7, y: 0.95, w: 2.3, h: 0.5, fontSize: 12, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: [0, 0, 0, 4] });
    s.addText(z.items.map((t, j) => ({ text: t, options: { breakLine: j < z.items.length - 1 } })), {
      x: x + 0.12, y: 1.52, w: 2.76, h: 3.1, fontSize: 11, color: C.dark, fontFace: "Calibri", paraSpaceAfter: 8,
    });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.1, y: 4.7, w: 2.8, h: 0.6, fill: { color: z.color, transparency: 85 }, line: { color: z.color, transparency: 50 } });
    s.addText(z.note, { x: x + 0.1, y: 4.7, w: 2.8, h: 0.6, fontSize: 9.5, italic: true, color: C.dark, fontFace: "Calibri", valign: "middle", align: "center", margin: 4 });
  });
}

// ── SLIDE 8: Roadmap ─────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Roadmap — Fases de Implementação", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: 2.65, w: 8.9, h: 0.06, fill: { color: C.accentDark }, line: { color: C.accentDark } });

  const steps = [
    { x: 0.4, label: "v0.1\nPoC Local", time: "Sem. 1–2", color: C.green, icon: "🧪" },
    { x: 2.6, label: "v1.0\nTJPR Shadow", time: "Mês 1–2", color: C.accent, icon: "📋" },
    { x: 4.8, label: "v1.1\nDocumentos", time: "Mês 3", color: "7C3AED", icon: "📝" },
    { x: 7.0, label: "v1.2\nContract AI", time: "Mês 4", color: C.amber, icon: "⚖️" },
    { x: 8.7, label: "v2.0\nMulti-user", time: "Trim 3+", color: C.gray, icon: "🏢" },
  ];

  steps.forEach((st) => {
    s.addShape(pres.shapes.OVAL, { x: st.x + 0.05, y: 2.35, w: 0.55, h: 0.55, fill: { color: st.color }, line: { color: st.color } });
    s.addText(st.icon, { x: st.x + 0.05, y: 2.35, w: 0.55, h: 0.55, fontSize: 16, align: "center", valign: "middle" });
    s.addText(st.time, { x: st.x - 0.2, y: 1.55, w: 1.0, h: 0.3, fontSize: 9, italic: true, color: C.gray, fontFace: "Calibri", align: "center" });
    s.addText(st.label, { x: st.x - 0.2, y: 1.88, w: 1.0, h: 0.42, fontSize: 10, bold: true, color: C.dark, fontFace: "Calibri", align: "center" });
  });

  const cards = [
    { x: 0.3, w: 2.1, title: "v0.1 · PoC", color: C.green, items: ["Dados fictícios", "Valida pipeline", "Zero risco"] },
    { x: 2.5, w: 2.1, title: "v1.0 · TJPR", color: C.accent, items: ["Diário Oficial", "Alertas de prazo", "Shadow mode"] },
    { x: 4.7, w: 2.1, title: "v1.1 · Docs", color: "7C3AED", items: ["Procurações", "Contratos", "Templates"] },
    { x: 6.9, w: 1.6, title: "v1.2+", color: C.amber, items: ["Contract AI", "M&A", "LGPD"] },
    { x: 8.55, w: 1.1, title: "v2.0", color: C.gray, items: ["Team", "Multi-user"] },
  ];

  cards.forEach((c) => {
    s.addShape(pres.shapes.RECTANGLE, { x: c.x, y: 3.1, w: c.w, h: 2.3, fill: { color: C.white }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: c.x, y: 3.1, w: c.w, h: 0.32, fill: { color: c.color }, line: { color: c.color } });
    s.addText(c.title, { x: c.x, y: 3.1, w: c.w, h: 0.32, fontSize: 10, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
    s.addText(c.items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < c.items.length - 1 } })), {
      x: c.x + 0.08, y: 3.48, w: c.w - 0.16, h: 1.85, fontSize: 10, color: C.gray, fontFace: "Calibri", paraSpaceAfter: 5,
    });
  });
}

// ── SLIDE 9: Custo & Infraestrutura ─────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Custo & Infraestrutura", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 1.0, w: 4.3, h: 4.35, fill: { color: C.lightBg }, line: { color: "D1D5DB" } });
  s.addText("💰  Custo Mensal Estimado", { x: 0.45, y: 1.1, w: 4.1, h: 0.4, fontSize: 13, bold: true, color: C.dark, fontFace: "Calibri" });

  const costs = [
    { item: "Claude Pro (Anthropic)", val: "~R$ 110/mês", note: "USD 20 — inclui crédito programático" },
    { item: "Infraestrutura local", val: "R$ 0", note: "Desktop existente do escritório" },
    { item: "Software / licenças", val: "R$ 0", note: "Claude for Legal é Apache 2.0 (gratuito)" },
    { item: "Manutenção técnica", val: "R$ 0", note: "Incluso no acordo de piloto" },
  ];

  costs.forEach((c, i) => {
    const y = 1.65 + i * 0.7;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.45, y, w: 4.1, h: 0.58, fill: { color: C.white }, line: { color: "E5E7EB" } });
    s.addText(c.item, { x: 0.55, y: y + 0.05, w: 2.2, h: 0.25, fontSize: 11, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(c.note, { x: 0.55, y: y + 0.3, w: 2.2, h: 0.22, fontSize: 9.5, italic: true, color: C.gray, fontFace: "Calibri" });
    s.addText(c.val, { x: 2.8, y: y + 0.1, w: 1.6, h: 0.35, fontSize: 13, bold: true, color: C.accent, fontFace: "Calibri", align: "right" });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.45, y: 4.45, w: 4.1, h: 0.65, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("TOTAL:", { x: 0.55, y: 4.45, w: 1.8, h: 0.65, fontSize: 12, bold: true, color: C.iceBlue, fontFace: "Calibri", valign: "middle" });
  s.addText("~R$ 110/mês", { x: 2.35, y: 4.45, w: 2.1, h: 0.65, fontSize: 16, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", align: "right" });

  s.addShape(pres.shapes.RECTANGLE, { x: 5.0, y: 1.0, w: 4.65, h: 4.35, fill: { color: C.lightBg }, line: { color: "D1D5DB" } });
  s.addText("🖥️  Requisitos de Infraestrutura", { x: 5.1, y: 1.1, w: 4.45, h: 0.4, fontSize: 13, bold: true, color: C.dark, fontFace: "Calibri" });

  const infra = [
    { label: "Desktop existente", ok: true, detail: "Windows 10/11 · 8GB RAM · SSD recomendado" },
    { label: "Conta Anthropic Pro", ok: true, detail: "Existente ou nova — USD 20/mês" },
    { label: "Conexão à internet", ok: true, detail: "Broadband padrão é suficiente" },
    { label: "Acesso Outlook / TJPR", ok: true, detail: "Credenciais existentes do escritório" },
    { label: "Workstation nova", ok: false, detail: "Não necessário — usa hardware existente" },
    { label: "Servidor dedicado", ok: false, detail: "Não necessário no piloto" },
  ];

  infra.forEach((inf, i) => {
    const y = 1.62 + i * 0.58;
    s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y, w: 4.45, h: 0.5, fill: { color: C.white }, line: { color: "E5E7EB" } });
    s.addText(inf.ok ? "✅" : "🚫", { x: 5.1, y, w: 0.4, h: 0.5, fontSize: 14, align: "center", valign: "middle" });
    s.addText(inf.label, { x: 5.5, y: y + 0.04, w: 2.1, h: 0.22, fontSize: 11, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(inf.detail, { x: 5.5, y: y + 0.26, w: 3.9, h: 0.2, fontSize: 9.5, italic: true, color: C.gray, fontFace: "Calibri" });
  });
}

// ── SLIDE 10: Próximos Passos ────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Próximos Passos — Formalização do Piloto", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 24, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  const steps = [
    { n: "1", title: "Responder §11", desc: "Tia May responde às perguntas técnicas pendentes: acesso remoto, desktop, conta Anthropic, Outlook TJPR, templates.", color: C.accent },
    { n: "2", title: "Formalização", desc: "Assinar: Contrato de prestação técnica · DPA (acordo de processamento de dados) · Termo de licença do plugin.", color: "7C3AED" },
    { n: "3", title: "v0.1 — PoC", desc: "Instalar ambiente local. Testar pipeline com dados fictícios. Validar cálculo de prazos e redação de peças sem dado real.", color: C.green },
    { n: "4", title: "v1.0 — Shadow", desc: "Conectar ao Diário TJPR. Rodar em shadow por 2 semanas. Tia May avalia alertas antes de qualquer ação automática.", color: C.navy },
  ];

  steps.forEach((st, i) => {
    const x = 0.3 + i * 2.38;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 2.2, h: 4.35, fill: { color: C.white }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.OVAL, { x: x + 0.75, y: 1.05, w: 0.7, h: 0.7, fill: { color: st.color }, line: { color: st.color } });
    s.addText(st.n, { x: x + 0.75, y: 1.05, w: 0.7, h: 0.7, fontSize: 18, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
    s.addText(st.title, { x: x + 0.1, y: 1.85, w: 2.0, h: 0.45, fontSize: 13, bold: true, color: C.dark, fontFace: "Calibri", align: "center" });
    s.addText(st.desc, { x: x + 0.12, y: 2.38, w: 1.96, h: 2.75, fontSize: 11, color: C.gray, fontFace: "Calibri" });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 5.1, w: 9.3, h: 0.38, fill: { color: "FEF9C3" }, line: { color: "FDE047" } });
  s.addText("⚠️  O piloto só começa após escopo, responsabilidades, suporte, licença, tratamento de dados e custos definidos por escrito.", {
    x: 0.45, y: 5.1, w: 9.1, h: 0.38, fontSize: 10.5, color: "854D0E", fontFace: "Calibri", valign: "middle",
  });
}

// ── SLIDE 11: Suite de Agentes — Visão Geral ────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.accentDark }, line: { color: C.accentDark } });
  s.addText("Suite de Agentes de IA — 48 Agentes · 6 Frentes", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 24, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });
  s.addText("Desenvolvido pela Escritório Parceiro · Integrado ao Claude Projects (claude.ai)", {
    x: 0.5, y: 0.92, w: 9, h: 0.32, fontSize: 12, color: C.iceBlue, fontFace: "Calibri", italic: true,
  });

  const frentes = [
    { n: "01", icon: "⏰", label: "Prazos &\nAcompanhamento", agents: 7, fase: "v1.0", color: "16A34A" },
    { n: "02", icon: "📝", label: "Petições\n& Peças", agents: 10, fase: "v1.1–v1.2", color: "2563EB" },
    { n: "03", icon: "⚖️", label: "Jurisprudência", agents: 9, fase: "v1.2–v1.3", color: "7C3AED" },
    { n: "04", icon: "🤝", label: "Atendimento\nao Cliente", agents: 5, fase: "v1.1–v1.2", color: C.amber },
    { n: "05", icon: "📄", label: "Contratos\n& Análise", agents: 10, fase: "v1.2–v1.4", color: "DC2626" },
    { n: "06", icon: "🏢", label: "Operação do\nEscritório", agents: 7, fase: "v1.0–v1.4", color: "0891B2" },
  ];

  frentes.forEach((f, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.3 + col * 3.15;
    const y = 1.35 + row * 1.95;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.0, h: 1.75, fill: { color: "1A2550" }, line: { color: f.color, width: 1.5 } });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: 1.75, fill: { color: f.color }, line: { color: f.color } });
    s.addText(f.icon, { x: x + 0.12, y: y + 0.1, w: 0.55, h: 0.55, fontSize: 20, align: "center" });
    s.addText(`Frente ${f.n}`, { x: x + 0.72, y: y + 0.08, w: 2.15, h: 0.25, fontSize: 9.5, color: f.color, fontFace: "Calibri", bold: true });
    s.addText(f.label, { x: x + 0.72, y: y + 0.32, w: 2.15, h: 0.5, fontSize: 12.5, color: C.white, fontFace: "Calibri", bold: true });
    s.addShape(pres.shapes.OVAL, { x: x + 0.12, y: y + 0.88, w: 0.55, h: 0.55, fill: { color: f.color }, line: { color: f.color } });
    s.addText(String(f.agents), { x: x + 0.12, y: y + 0.88, w: 0.55, h: 0.55, fontSize: 14, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
    s.addText("agentes", { x: x + 0.72, y: y + 0.92, w: 1.0, h: 0.22, fontSize: 10, color: "8899CC", fontFace: "Calibri" });
    s.addText(f.fase, { x: x + 0.72, y: y + 1.14, w: 1.5, h: 0.22, fontSize: 9.5, italic: true, color: "8899CC", fontFace: "Calibri" });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 3.3, y: 5.1, w: 3.4, h: 0.38, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("TOTAL: 48 AGENTES · 6 FRENTES · 100% NO CLAUDE", { x: 3.3, y: 5.1, w: 3.4, h: 0.38, fontSize: 10.5, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
}

// ── SLIDE 12: Frente 1 — Prazos ──────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: "16A34A" }, line: { color: "16A34A" } });
  s.addText("⏰  Frente 01 · Prazos & Acompanhamento", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 24, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });
  s.addText("7 agentes · Fase v1.0 · MCP: tjpr-diario-parser + cpc-2015-prazos", { x: 0.5, y: 0.9, w: 9, h: 0.3, fontSize: 11, color: C.gray, fontFace: "Calibri", italic: true });

  const agents = [
    { name: "Monitor DJE/TJPR", desc: "Lê diário diariamente, extrai intimações do escritório" },
    { name: "Extrator Intimação", desc: "Identifica tipo, número de processo e parte" },
    { name: "Calc Prazo CPC", desc: "Aplica arts. 219/231/183, contagem em dias úteis" },
    { name: "Dobro Fazenda", desc: "Identifica Fazenda Pública e aplica prazo em dobro" },
    { name: "Recesso Forense", desc: "Desconta recesso TJPR / STJ / STF automaticamente" },
    { name: "Lembrete WhatsApp", desc: "Push para prazos urgentes (≤ 3 dias) via bridge" },
    { name: "Relatório Diário", desc: "CSV urgentes + CSV prazos + PDF resumo executivo" },
  ];

  agents.forEach((a, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = col === 0 ? 0.3 : 5.15;
    const y = 1.35 + row * 1.05;
    const w = 4.7;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.88, fill: { color: C.white }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: 0.88, fill: { color: "16A34A" }, line: { color: "16A34A" } });
    s.addShape(pres.shapes.OVAL, { x: x + 0.12, y: y + 0.18, w: 0.38, h: 0.38, fill: { color: "16A34A" }, line: { color: "16A34A" } });
    s.addText(String(i + 1), { x: x + 0.12, y: y + 0.18, w: 0.38, h: 0.38, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
    s.addText(a.name, { x: x + 0.6, y: y + 0.07, w: w - 0.75, h: 0.32, fontSize: 12.5, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(a.desc, { x: x + 0.6, y: y + 0.44, w: w - 0.75, h: 0.35, fontSize: 10.5, color: C.gray, fontFace: "Calibri" });
  });
}

// ── SLIDE 13: Frente 2 — Petições ────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: "2563EB" }, line: { color: "2563EB" } });
  s.addText("📝  Frente 02 · Petições & Peças", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 24, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });
  s.addText("10 agentes · Fase v1.1–v1.2 · MCP: practice-profile + pii-redactor-br", { x: 0.5, y: 0.9, w: 9, h: 0.3, fontSize: 11, color: C.gray, fontFace: "Calibri", italic: true });

  const agents = [
    { name: "Petição Inicial Cível", desc: "Gera inicial a partir de fatos + causa de pedir", fase: "v1.1" },
    { name: "Contestação", desc: "Gera contestação com teses padrão do escritório", fase: "v1.1" },
    { name: "Réplica", desc: "Responde contestação adversa automaticamente", fase: "v1.1" },
    { name: "Embargos de Declaração", desc: "Identifica omissão/contradição e gera ED", fase: "v1.1" },
    { name: "Manifestação Genérica", desc: "Peça avulsa para qualquer movimentação processual", fase: "v1.1" },
    { name: "Apelação", desc: "Estrutura razões com fundamentos TJPR", fase: "v1.2" },
    { name: "Contrarrazões", desc: "Contra-argumenta apelação adversa", fase: "v1.2" },
    { name: "Agravo de Instrumento", desc: "Gera AI com requisitos formais TJPR", fase: "v1.2" },
    { name: "Exceção de Incompetência", desc: "Gera com fundamento territorial/material", fase: "v1.2" },
    { name: "Impugnação à Gratuidade", desc: "Analisa e impugna pedido de justiça gratuita", fase: "v1.2" },
  ];

  agents.forEach((a, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = col === 0 ? 0.3 : 5.15;
    const y = 1.32 + row * 0.83;
    const w = 4.7;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.72, fill: { color: C.white }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: 0.72, fill: { color: "2563EB" }, line: { color: "2563EB" } });
    s.addText(String(i + 1), { x: x + 0.1, y: y + 0.13, w: 0.32, h: 0.32, fontSize: 9, bold: true, color: "2563EB", fontFace: "Calibri", align: "center", valign: "middle" });
    s.addText(a.name, { x: x + 0.48, y: y + 0.05, w: w - 0.85, h: 0.28, fontSize: 11.5, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(a.desc, { x: x + 0.48, y: y + 0.36, w: w - 0.95, h: 0.28, fontSize: 10, color: C.gray, fontFace: "Calibri" });
    s.addText(a.fase, { x: x + w - 0.68, y: y + 0.05, w: 0.6, h: 0.22, fontSize: 8.5, italic: true, color: "2563EB", fontFace: "Calibri", align: "right" });
  });
}

// ── SLIDE 14: Frentes 3 + 4 ──────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("⚖️  Frente 03 · Jurisprudência   |   🤝  Frente 04 · Atendimento ao Cliente", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 19, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  // Frente 3
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.95, w: 4.5, h: 0.38, fill: { color: "7C3AED" }, line: { color: "7C3AED" } });
  s.addText("9 agentes · v1.2–v1.3", { x: 0.3, y: 0.95, w: 4.5, h: 0.38, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: [0,0,0,8] });

  const juri = [
    ["Busca TJPR", "Acórdãos TJPR por tese/número"],
    ["Busca STJ", "Filtra por turma/seção"],
    ["Busca STF", "Filtra repercussão geral"],
    ["Busca TRF4", "Federal região sul"],
    ["Filtro por Tese", "Agrupa por tese jurídica"],
    ["Ementário", "Formata para colar na peça"],
    ["Súmulas Aplicáveis", "Vinculantes + persuasivas"],
    ["Precedentes Bancários", "Bancário + CDC especializado"],
    ["Distinguishing", "Aponta distinções com precedente"],
  ];
  juri.forEach(([name, desc], i) => {
    const y = 1.42 + i * 0.44;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y, w: 4.5, h: 0.38, fill: { color: i % 2 === 0 ? C.lightBg : C.white }, line: { color: "E5E7EB" } });
    s.addText(`${i + 1}. ${name}`, { x: 0.38, y: y + 0.04, w: 1.9, h: 0.28, fontSize: 10.5, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(desc, { x: 2.32, y: y + 0.04, w: 2.38, h: 0.28, fontSize: 9.5, color: C.gray, fontFace: "Calibri" });
  });

  // Frente 4
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 0.95, w: 4.5, h: 0.38, fill: { color: C.amber }, line: { color: C.amber } });
  s.addText("5 agentes · v1.1–v1.2", { x: 5.2, y: 0.95, w: 4.5, h: 0.38, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: [0,0,0,8] });

  const client = [
    ["Triagem Novo Caso", "Qualifica caso via formulário estruturado"],
    ["Orientação Inicial", "Resposta padrão + próximos passos"],
    ["Onboarding Cliente", "Gera contrato honorários + procuração"],
    ["Proposta Honorários", "Calcula faixa por tipo de causa"],
    ["Follow-up Processo", "Atualiza cliente sobre movimentação"],
  ];
  client.forEach(([name, desc], i) => {
    const y = 1.42 + i * 0.44;
    s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y, w: 4.5, h: 0.38, fill: { color: i % 2 === 0 ? C.lightBg : C.white }, line: { color: "E5E7EB" } });
    s.addText(`${i + 1}. ${name}`, { x: 5.28, y: y + 0.04, w: 1.9, h: 0.28, fontSize: 10.5, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(desc, { x: 7.22, y: y + 0.04, w: 2.38, h: 0.28, fontSize: 9.5, color: C.gray, fontFace: "Calibri" });
  });
}

// ── SLIDE 15: Frente 5 — Contratos ───────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: "DC2626" }, line: { color: "DC2626" } });
  s.addText("📄  Frente 05 · Contratos & Análise", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 24, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });
  s.addText("10 agentes · Fase v1.2–v1.4 · MCP: pii-redactor-br + lgpd-specifics", { x: 0.5, y: 0.9, w: 9, h: 0.3, fontSize: 11, color: C.gray, fontFace: "Calibri", italic: true });

  const agents = [
    { name: "Análise Contrato Bancário", desc: "Identifica cláusulas abusivas CDC/BACEN", fase: "v1.2" },
    { name: "Cláusulas Abusivas", desc: "Lista e fundamenta abusividade juridicamente", fase: "v1.2" },
    { name: "Revisão Financiamento", desc: "Analisa spread, indexador, capitalização", fase: "v1.2" },
    { name: "NDA Review", desc: "Analisa cláusulas de confidencialidade", fase: "v1.2" },
    { name: "Distrato", desc: "Gera distrato com base no contrato original", fase: "v1.2" },
    { name: "Relatório de Risco", desc: "Pontua riscos, sugere redação alternativa", fase: "v1.2" },
    { name: "Renewal Watcher", desc: "Monitora vencimentos de contratos ativos", fase: "v1.2" },
    { name: "Análise Societário", desc: "Cotas, responsabilidade, quórum decisório", fase: "v1.3" },
    { name: "Due Diligence", desc: "Checklist CVM / Junta / Receita Federal", fase: "v1.3" },
    { name: "LGPD Compliance Check", desc: "Verifica DPA, consentimento, bases legais LGPD", fase: "v1.4" },
  ];

  agents.forEach((a, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = col === 0 ? 0.3 : 5.15;
    const y = 1.32 + row * 0.83;
    const w = 4.7;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.72, fill: { color: C.white }, line: { color: "D1D5DB" }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: 0.72, fill: { color: "DC2626" }, line: { color: "DC2626" } });
    s.addText(String(i + 1), { x: x + 0.1, y: y + 0.13, w: 0.32, h: 0.32, fontSize: 9, bold: true, color: "DC2626", fontFace: "Calibri", align: "center", valign: "middle" });
    s.addText(a.name, { x: x + 0.48, y: y + 0.05, w: w - 0.85, h: 0.28, fontSize: 11.5, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(a.desc, { x: x + 0.48, y: y + 0.36, w: w - 0.95, h: 0.28, fontSize: 10, color: C.gray, fontFace: "Calibri" });
    s.addText(a.fase, { x: x + w - 0.68, y: y + 0.05, w: 0.6, h: 0.22, fontSize: 8.5, italic: true, color: "DC2626", fontFace: "Calibri", align: "right" });
  });
}

// ── SLIDE 16: Frente 6 + Mapeamento por Fase ─────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: "0891B2" }, line: { color: "0891B2" } });
  s.addText("🏢  Frente 06 · Operação do Escritório   |   Agentes por Fase", { x: 0.5, y: 0, w: 9, h: 0.85, fontSize: 20, bold: true, color: C.white, fontFace: "Calibri", valign: "middle" });

  const ops = [
    { name: "Backup Audit Log", desc: "Verifica integridade da cadeia de auditoria", fase: "v1.0" },
    { name: "Agenda Audiência", desc: "Estrutura pauta + documentos necessários", fase: "v1.1" },
    { name: "Resumo de Processo", desc: "Síntese cronológica do processo", fase: "v1.1" },
    { name: "Política de Uso IA", desc: "Registra consentimento + treina equipe", fase: "v1.1" },
    { name: "Relatório Semanal", desc: "Consolida prazos + andamentos + pendências", fase: "v1.1" },
    { name: "Cobrança Honorários", desc: "Régua de cobrança automática", fase: "v1.2" },
    { name: "LGPD Audit", desc: "Verifica conformidade da operação", fase: "v1.4" },
  ];

  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.95, w: 4.5, h: 0.35, fill: { color: "0891B2" }, line: { color: "0891B2" } });
  s.addText("7 agentes · v1.0–v1.4", { x: 0.3, y: 0.95, w: 4.5, h: 0.35, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: [0,0,0,8] });

  ops.forEach((a, i) => {
    const y = 1.38 + i * 0.6;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y, w: 4.5, h: 0.5, fill: { color: i % 2 === 0 ? C.lightBg : C.white }, line: { color: "E5E7EB" } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y, w: 0.05, h: 0.5, fill: { color: "0891B2" }, line: { color: "0891B2" } });
    s.addText(`${i + 1}. ${a.name}`, { x: 0.42, y: y + 0.04, w: 2.5, h: 0.22, fontSize: 11, bold: true, color: C.dark, fontFace: "Calibri" });
    s.addText(a.desc, { x: 0.42, y: y + 0.27, w: 2.8, h: 0.18, fontSize: 9.5, color: C.gray, fontFace: "Calibri" });
    s.addText(a.fase, { x: 3.5, y: y + 0.13, w: 1.2, h: 0.2, fontSize: 9.5, italic: true, color: "0891B2", fontFace: "Calibri", align: "right" });
  });

  // Right: mapeamento por fase (bar chart manual)
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 0.95, w: 4.5, h: 0.35, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("Crescimento de Agentes por Fase", { x: 5.2, y: 0.95, w: 4.5, h: 0.35, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: [0,0,0,8] });

  const fases = [
    { fase: "v0.1 PoC", n: "0",  label: "Infra (dev only)",               color: C.gray,     pct: 0.0 },
    { fase: "v1.0",     n: "8",  label: "Frentes 1 + 6 (parcial)",         color: "16A34A",   pct: 0.17 },
    { fase: "v1.1",     n: "22", label: "Frentes 2 (parcial) + 4 + 6",     color: "2563EB",   pct: 0.46 },
    { fase: "v1.2",     n: "43", label: "Frentes 2 + 3 + 5 (parcial) + 6", color: "7C3AED",   pct: 0.90 },
    { fase: "v1.3",     n: "46", label: "Frente 5 (M&A/DD) + 3",           color: C.amber,    pct: 0.96 },
    { fase: "v1.4",     n: "48", label: "Frentes 5 + 6 (LGPD completo)",   color: "DC2626",   pct: 1.0  },
  ];

  const maxBarW = 3.5;
  fases.forEach((f, i) => {
    const y = 1.38 + i * 0.66;
    s.addText(f.fase, { x: 5.25, y, w: 0.75, h: 0.28, fontSize: 10, bold: true, color: C.dark, fontFace: "Calibri", valign: "middle" });
    if (f.pct > 0) {
      s.addShape(pres.shapes.RECTANGLE, { x: 6.05, y: y + 0.04, w: f.pct * maxBarW, h: 0.22, fill: { color: f.color }, line: { color: f.color } });
    }
    s.addText(f.n, { x: 6.05 + f.pct * maxBarW + 0.05, y, w: 0.4, h: 0.28, fontSize: 11, bold: true, color: f.color, fontFace: "Calibri", valign: "middle" });
    s.addText(f.label, { x: 5.25, y: y + 0.3, w: 4.4, h: 0.2, fontSize: 9, color: C.gray, fontFace: "Calibri", italic: true });
  });
}

// ── SLIDE 17: Encerramento ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.OVAL, { x: -1, y: 3.5, w: 4, h: 4, fill: { color: C.accentDark, transparency: 60 }, line: { color: C.accentDark, transparency: 60 } });
  s.addShape(pres.shapes.OVAL, { x: 8, y: -1, w: 3.5, h: 3.5, fill: { color: C.accent, transparency: 55 }, line: { color: C.accent, transparency: 55 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.35, h: 5.625, fill: { color: C.accent }, line: { color: C.accent } });

  s.addText("Obrigado.", { x: 0.7, y: 1.2, w: 8.5, h: 1.0, fontSize: 52, bold: true, color: C.white, fontFace: "Calibri" });
  s.addText("Aguardamos suas respostas ao §11 para iniciarmos a formalização.", { x: 0.7, y: 2.3, w: 8.5, h: 0.55, fontSize: 18, color: C.iceBlue, fontFace: "Calibri" });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 3.1, w: 5.5, h: 0.04, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("📧  enzombromanus@gmail.com", { x: 0.7, y: 3.25, w: 8.5, h: 0.45, fontSize: 14, color: C.iceBlue, fontFace: "Calibri" });
  s.addText("📄  Documentos completos disponíveis mediante solicitação", { x: 0.7, y: 3.75, w: 8.5, h: 0.4, fontSize: 14, color: C.iceBlue, fontFace: "Calibri" });
  s.addText("LegalOps BR  ·  Confidencial  ·  Maio 2026", { x: 0.7, y: 5.1, w: 8.5, h: 0.35, fontSize: 11, color: "6677AA", fontFace: "Calibri" });
}

pres.writeFile({ fileName: "/home/bossmann/OneDrive/Mafioso/10 - Projetos/LegalOps/LegalOps_BR_Tia_May.pptx" })
  .then(() => console.log("DONE: LegalOps_BR_Tia_May.pptx"))
  .catch((e) => { console.error("ERROR:", e); process.exit(1); });
