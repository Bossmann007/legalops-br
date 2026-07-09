---
name: briefing
description: Prazos urgentes do dia + agenda + alertas
triggers: ["/briefing", "prazos do dia", "o que tenho hoje", "agenda hoje"]
---

Execute em sequência:

## 1. Prazos Urgentes
Para cada intimação/texto disponível, extraia com `parse` e calcule com `prazo`:
```bash
uv run legalops parse --input "[arquivo-texto]"
uv run legalops prazo --data-publicacao AAAA-MM-DD --prazo-dias N --parte particular --tribunal TJPR --hoje AAAA-MM-DD
```
Apresente em semáforo:
- 🔴 **URGENTE** — vence hoje ou amanhã
- 🟡 **ATENÇÃO** — vence em 2–3 dias
- 🟢 **OK** — vence em >3 dias

Se houver prazos vermelhos: destaque no topo antes de qualquer outra coisa.

## 2. Processos com Movimentação Nova
Para textos colados/scraped de tribunais:
```bash
uv run legalops tribunal-detect --input "[arquivo-texto]" --sender "[remetente-opcional]"
uv run legalops parse --input "[arquivo-texto]"
```
Apresente: número do processo (mascarado), tribunal, tipo de movimentação.

## 3. DSARs Pendentes
Não há subcomando de status/listagem de DSAR ainda. Se houver arquivo de solicitação:
```bash
uv run legalops dsar --input "[arquivo-solicitacao-redigida]" --request-id DSAR-XXX --titular-ref TIT-XXX --recebimento AAAA-MM-DD --hoje AAAA-MM-DD
```
Se houver: listar com data de recebimento (prazo LGPD = 15 dias).

## 4. Contratos em Renovação
```bash
uv run legalops renovacao --hoje AAAA-MM-DD
```

## 5. Auditoria
```bash
uv run legalops audit verify --db "[audit.db]"
```

## 6. Formato final
```
DRAFT — Requer revisão e assinatura

⚖️ Briefing — [data]

🔴 URGENTE (N prazos)
  • [tipo de ato] — [CLI-XXX] — vence [data]

📋 Processos com novidade (N)
  • [CNJ mascarado] TJXX — [tipo movimentação]

📊 KPIs rápidos
  • [N] processos ativos · [honorarios/clientes: subcomando pendente — segunda onda] · Próxima audiência: [data]
```

Se API offline: "Engine offline — verifique se o servidor está rodando."
