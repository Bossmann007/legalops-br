---
name: revisao-semanal
description: Reunião semanal completa — operações + mercado jurídico + melhorias + novidades IA
triggers: ["/revisao", "/revisao-semanal", "revisão da semana", "como foi a semana", "reunião semanal"]
---

Execute em sequência:

## 1. OPERAÇÕES DA SEMANA
```bash
uv run legalops honorarios --relatorio-mensal --semana-atual
uv run legalops prazos --stats --semana-atual
uv run legalops processos --movimentacoes --semana-atual
uv run legalops dsar --pendentes
```

Apresente:
- Honorários recebidos vs semana anterior
- Prazos: cumpridos / perdidos / próximos 7 dias
- Processos com movimentação (por tribunal)
- DSARs: abertos / respondidos / vencendo
- Leads no WhatsApp: respondidos / perdidos

## 2. CLIENTES EM RISCO
```bash
uv run legalops clientes --sem-atualizacao-dias 30
uv run legalops renovacao --vencendo-em 60
```

Apresente:
- Clientes sem contato há >30 dias → sugerir check-in
- Contratos vencendo → sugerir renovação antecipada

## 3. MERCADO JURÍDICO
Use WebSearch para:
- "jurisprudência [área principal do escritório] [mês atual]"
- "LGPD multas ANPD [ano atual]"
- "OAB novas resoluções [ano atual]"
- "advocacia trabalhista tendências Brasil"

Apresente: top 3 insights relevantes para o escritório

## 4. NOVIDADES DE IA E FERRAMENTAS
Busque:
- Novidades do Claude (anthropic.com/news)
- Novas ferramentas jurídicas com IA no Brasil
- Atualizações do LegalOps engine (changelog)

Apresente: o que melhorou, o que impacta o harness

## 5. SUGESTÕES DE MELHORIA
Com base nos dados da semana, sugira 2–3 ações concretas:
- "N clientes inativos — campanha de check-in?"
- "Contrato [CLI-XXX] vence em Y dias — renovar agora?"
- "Prazo [tipo] apareceu 3x essa semana — criar template?"

## 6. PRÓXIMA SEMANA
Confirmar prioridades.
Agendar lembretes se necessário.

Encerre com: "Revisão concluída. Quer executar alguma das ações sugeridas agora?"
