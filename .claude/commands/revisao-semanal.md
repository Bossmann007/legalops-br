---
name: revisao-semanal
description: Reunião semanal completa — operações + mercado jurídico + melhorias + novidades IA
triggers: ["/revisao", "/revisao-semanal", "revisão da semana", "como foi a semana", "reunião semanal"]
---

## Proveniência obrigatória
Na saída, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Resultado do
CLI recebe `[motor determinístico]` quando houver cálculo jurídico; conteúdo de registro local
fornecido recebe `[documento do usuário]`; pesquisa não oficial recebe
`[fonte secundária — conferir]`; e análise não conferida recebe
`[conhecimento do modelo — conferir]`. Uma etiqueta geral não basta.

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

Apresente **SÓ o que tem fonte real** — nunca invente número. Sem store → escreva
"[sem registro — não rastreado]", não estime:
- Honorários: do ledger `data/honorarios.json` se existir; senão "[sem registro]"
- Prazos próximos 7 dias: dos que ela anotou; "cumpridos/perdidos" NÃO são rastreados
  automaticamente → "[sem registro — controle oficial é o PJe]"
- Processos com movimentação: só dos textos que ela colou nesta semana
- DSARs: do registro manual dela; senão "[sem registro]"
- Contratos vencendo: de `renovacao` (fonte real)

## 2. CLIENTES EM RISCO
Clientes sem atualização ainda não têm subcomando. Fazer resumo por leitura/raciocínio do Claude e marcar `[honorarios/clientes: subcomando pendente — segunda onda]`.
```bash
uv run legalops renovacao --hoje AAAA-MM-DD --incluir-ok
```

Apresente:
- Clientes sem contato há >30 dias: **não há store de último-contato** → não invente lista;
  diga "[sem rastreamento de contato — pendente]" e, se ela quiser, ajude a montar manualmente.
- Contratos vencendo → de `renovacao` (fonte real), sugerir renovação antecipada

## 3. MERCADO JURÍDICO
Use WebSearch para (áreas reais dela — bancário/financeiro, digital/LGPD, médico/saúde):
- "jurisprudência [área do escritório] [mês atual]"
- "LGPD multas ANPD [ano atual]"
- "OAB novas resoluções [ano atual]"
- "fraude bancária / mercado de capitais tendências Brasil"

Apresente: top 3 insights. **São notícias, NÃO fonte jurídica** — marque cada citação como
"a confirmar na fonte primária"; nunca trate resultado de busca como direito vigente (RULES #3).

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
