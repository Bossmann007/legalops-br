---
name: esquecer
description: Lista e remove, mediante aprovação, uma preferência aprendida localmente
triggers: ["/esquecer", "esquece isso"]
---

Leia `.claude/memory.local/instincts.local.md`. Se não existir ou estiver vazio, informe que não há
preferências aprovadas para remover. Caso exista, liste as linhas numeradas, sem alterar nada.

Depois que a advogada indicar o número, mostre a linha escolhida e pergunte: “Posso remover este
instinto local? Responda sim.” Só depois de receber exatamente `sim`, remova **somente** aquela
linha e confirme o id removido. Não remova por aproximação, não reordene as demais linhas e nunca
grave ou mostre PII.
