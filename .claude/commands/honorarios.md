---
name: honorarios
description: Controle de honorários — fechar mês, inadimplências, relatório
triggers: ["/honorarios", "fechar mês", "relatório financeiro", "quanto recebi", "inadimplência"]
---

> Não há subcomando `legalops honorarios` no engine (recurso da 2ª onda — pendente).
> Até lá, este controle é feito pelo Claude lendo/escrevendo um **ledger local**:
> `data/honorarios.json` (gitignored, nunca versionado, só aliases de cliente).
> Toda saída financeira começa com `DRAFT — Requer revisão`.

## Ledger local (data/honorarios.json)
Lista de lançamentos, cada um:
`{"alias": "CLI-XXX", "caso": "[desc curta]", "valor": N, "forma": "pix|transferencia|boleto|dinheiro", "data_vencimento": "AAAA-MM-DD", "status": "pago|pendente", "data_pagamento": "AAAA-MM-DD|null"}`
Cliente **sempre** por alias — nunca nome real. Se o arquivo não existir, crie-o vazio (`[]`).

## Fechar o mês
1. Leia `data/honorarios.json`.
2. Filtre lançamentos do mês pedido e apresente (DRAFT):
   - Total recebido (status=pago no mês) · por forma de pagamento · por área · por cliente (alias)
   - Pendências (status=pendente) · comparação com mês anterior se houver dado
3. Não invente números — se o ledger estiver vazio, diga e ofereça registrar o primeiro.

## Registrar honorário
Colete: alias (`CLI-XXX`), caso (descrição breve), valor, forma, vencimento, parcelamento se houver.
Anexe o lançamento a `data/honorarios.json`. Confirme com ela antes de salvar.

## Inadimplência
Filtre `status=pendente` com `data_vencimento` já passada. Para cada um, ofereça um **rascunho**
de mensagem de cobrança (tom profissional, sem constranger) — ela revisa e envia por conta própria.
Nada é enviado pelo sistema.

## Relatório anual
Agregue o ledger do ano pedido (mesmos cortes do fechamento mensal), sempre DRAFT.
