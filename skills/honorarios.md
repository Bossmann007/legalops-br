---
name: honorarios
description: Controle de honorários — fechar mês, inadimplências, relatório
triggers: ["/honorarios", "fechar mês", "relatório financeiro", "quanto recebi", "inadimplência"]
---

## Para Fechar o Mês
```bash
uv run legalops honorarios --relatorio-mensal --mes [AAAA-MM]
```

Apresente:
- Total recebido no mês
- Por forma de pagamento (Pix / transferência / boleto / dinheiro)
- Por área (trabalhista / civil / família / etc.)
- Por cliente (aliases — `CLI-XXX`)
- Pendências (status=pendente)
- Comparação com mês anterior se disponível

## Para Registrar Honorário
Colete:
1. Cliente (alias `CLI-XXX` — nunca nome real)
2. Caso (número interno ou descrição breve)
3. Valor combinado
4. Forma de pagamento
5. Parcelamento? (se sim: quantas parcelas, datas)

```bash
uv run legalops honorarios --registrar \
  --cliente CLI-XXX \
  --caso "[desc]" \
  --valor [N] \
  --forma [pix|transferencia|boleto|dinheiro] \
  --data-vencimento AAAA-MM-DD
```

## Alertas de Inadimplência
```bash
uv run legalops honorarios --inadimplentes --vencido-ha 7
```

Para cada inadimplente: sugerir template de cobrança via WhatsApp (sem constranger — tom profissional).

## Relatório Anual
```bash
uv run legalops honorarios --relatorio-anual --ano [AAAA]
```

Encerre com: "Relatório salvo. Deseja exportar em PDF?"
