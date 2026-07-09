---
name: revisao-semanal
description: Reunião semanal completa — operações + mercado jurídico + melhorias + novidades IA
triggers: ["/revisao", "/revisao-semanal", "revisão da semana", "como foi a semana", "reunião semanal"]
---

Execute em sequência:

## 1. OPERAÇÕES DA SEMANA
Use comandos reais quando houver backing no engine:
```bash
uv run legalops audit verify --db "[audit.db]"
uv run legalops renovacao --hoje AAAA-MM-DD --incluir-ok
uv run legalops tribunal-detect --input "[arquivo-texto]" --sender "[remetente-opcional]"
uv run legalops parse --input "[arquivo-texto]"
uv run legalops prazo --data-publicacao AAAA-MM-DD --prazo-dias N --parte particular --tribunal TJPR --hoje AAAA-MM-DD
```
Para honorarios/clientes, fazer resumo por leitura/raciocínio do Claude e marcar: `[honorarios/clientes: subcomando pendente — segunda onda]`.
Para DSARs, usar arquivos/registro manual existente e, quando houver solicitação individual, `legalops dsar --input ... --request-id ... --titular-ref ... --recebimento ... --hoje ...`.

Apresente:
- Honorários recebidos vs semana anterior
- Prazos: cumpridos / perdidos / próximos 7 dias
- Processos com movimentação (por tribunal)
- DSARs: abertos / respondidos / vencendo
- Leads no WhatsApp: respondidos / perdidos

## 2. CLIENTES EM RISCO
Clientes sem atualização ainda não têm subcomando. Fazer resumo por leitura/raciocínio do Claude e marcar `[honorarios/clientes: subcomando pendente — segunda onda]`.
```bash
uv run legalops renovacao --hoje AAAA-MM-DD --incluir-ok
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

## Formato inicial obrigatório
Toda saída deve começar com:
```
DRAFT — Requer revisão e assinatura
```

Encerre com: "Revisão concluída. Quer executar alguma das ações sugeridas agora?"
