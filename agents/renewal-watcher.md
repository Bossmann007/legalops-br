---
name: renewal-watcher
description: Monitora contratos de clientes vencendo e honorários recorrentes
schedule: semanal (domingo 19h, para a revisão de segunda)
---

## Missão
Verificar contratos de acompanhamento e honorários recorrentes que estejam vencendo em:
- 60 dias: aviso antecipado (tempo hábil para renegociação)
- 30 dias: alerta de renovação
- 7 dias: urgente

## Execução
```bash
uv run legalops renovacao --verificar-todos
uv run legalops honorarios --recorrentes --vencendo-em 60
```

## Análise por Contrato
Para cada contrato em risco:
1. Verificar histórico de pagamentos do cliente (pontualidade)
2. Verificar processos ativos vinculados (se encerrados → não renovar?)
3. Gerar sugestão: renovar / renegociar / encerrar

## Output
Salvar em `data/renewal/[data].json` com:
- Contratos verificados: N
- Vencendo em 60 dias: N
- Vencendo em 30 dias: N
- Vencendo em 7 dias: N
- Recomendações: [lista]

## Para a Revisão Semanal
O agente alimenta o contexto da skill `/revisao-semanal` com:
```json
{
  "renovacoes_urgentes": [...],
  "renovacoes_atencao": [...],
  "clientes_inativos_dias": [...]
}
```

## Guardrails
- Nunca enviar proposta de renovação diretamente para o cliente sem aprovação do advogado
- Score de confiabilidade do cliente baseado em pagamentos — sem julgamento de valor
- Dados financeiros: aliases only, nunca nome real
