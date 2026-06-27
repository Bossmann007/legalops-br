---
name: briefing
description: Prazos urgentes do dia + agenda + alertas
triggers: ["/briefing", "prazos do dia", "o que tenho hoje", "agenda hoje"]
---

Execute em sequência:

## 1. Prazos Urgentes
```bash
uv run legalops prazos --vencendo-em 3
```
Apresente em semáforo:
- 🔴 **URGENTE** — vence hoje ou amanhã
- 🟡 **ATENÇÃO** — vence em 2–3 dias
- 🟢 **OK** — vence em >3 dias

Se houver prazos vermelhos: destaque no topo antes de qualquer outra coisa.

## 2. Processos com Movimentação Nova
```bash
uv run legalops processos --movimentacao-hoje
```
Apresente: número do processo (mascarado), tribunal, tipo de movimentação.

## 3. DSARs Pendentes
```bash
uv run legalops dsar --status pendente
```
Se houver: listar com data de recebimento (prazo LGPD = 15 dias).

## 4. Formato final
```
⚖️ Briefing — [data]

🔴 URGENTE (N prazos)
  • [tipo de ato] — [CLI-XXX] — vence [data]

📋 Processos com novidade (N)
  • [CNJ mascarado] TJXX — [tipo movimentação]

📊 KPIs rápidos
  • [N] processos ativos · [N] clientes · Próxima audiência: [data]
```

Se API offline: "Engine offline — verifique se o servidor está rodando."
