---
name: briefing
description: Prazos urgentes do dia + agenda + alertas
triggers: ["/briefing", "prazos do dia", "o que tenho hoje", "agenda hoje"]
---

Execute em sequência:

## 1. Prazos Urgentes
Primeiro, o estado da última varredura (não-olhei ≠ nada-novo):
```bash
uv run legalops scan-state --get --hoje AAAA-MM-DD
```
Mostre a faixa de varredura ANTES dos prazos: se `estado` for `falha`, abra com o banner
vermelho e NÃO diga "sem prazos"; se `nunca`, sugira `/varrer` antes de afirmar que não há nada.

Depois leia os prazos locais registrados (rede de segurança; não é fonte oficial):
```bash
uv run legalops prazos --ate 7 --hoje AAAA-MM-DD
```
Para cada intimação/texto novo disponível, extraia com `parse` e calcule com `prazo`:
```bash
uv run legalops parse --input "[arquivo-texto]"
uv run legalops prazo --data-publicacao AAAA-MM-DD --prazo-dias N --parte particular --tribunal TJPR --hoje AAAA-MM-DD
```
Se a advogada quiser acompanhar esse cálculo no painel, salvar explicitamente com
`--salvar --ref PROC-XXX --ato "[desc]"`. Isso grava apenas em `data/prazos.json`;
não agenda alerta automático e não substitui conferência no PJe/Projudi.
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
Se houver: listar com data de recebimento, SLA interno e nota para confirmar prazo aplicável em fonte primária.

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

Se algum comando `legalops` falhar (não há servidor — é um programa local): diga em linguagem
simples que aquele cálculo não rodou, mostre o resto do briefing, e lembre de conferir prazos
no PJe. Nunca peça para ela "verificar servidor" — não existe.

➡️ Próximo: `/varrer` se ainda não checou a caixa hoje · `/painel` para o quadro completo.
