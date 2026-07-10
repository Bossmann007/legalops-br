---
name: encerrar
description: Salva um resumo PII-free para retomar o trabalho na próxima sessão
triggers: ["/encerrar", "fechar sessão", "tchau", "terminei"]
---

Use quando a advogada terminar a sessão. O resumo é local e PII-free; ele registra apenas estado
operacional, aliases, fluxo e pendências — nunca nome, CPF, OAB ou processo real.

## Gate de aprovação

1. Leia o Primer, os prazos locais e as pendências disponíveis.
2. Mostre uma proposta curta com as quatro seções: `Estado Operacional`, `Prazos Críticos`,
   `Threads Abertos` e `Próxima Sessão`.
3. Pergunte: “Posso salvar este resumo local PII-free e registrar a lição da sessão? Responda
   sim.”
4. Só depois de receber exatamente `sim`, faça a gravação abaixo. Sem `sim`, não altere arquivo.

## Ao receber “sim”

1. Se `.claude/memory.local/primer.local.md` não existir, copie primeiro
   `.claude/memory/Primer.md`; depois atualize somente as quatro seções propostas.
2. Faça append de **uma** linha JSONL PII-free em
   `.claude/memory.local/hindsight.local.md`, sem reescrever o histórico:

```json
{"date":"AAAA-MM-DD","last_task":"...","open_threads":"...","lesson":"..."}
```

3. Confirme objetivamente quais seções foram salvas e que uma linha foi acrescentada ao histórico.
