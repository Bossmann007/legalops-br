---
name: aprender
description: Propõe salvar uma preferência PII-free aprovada pela advogada
triggers: ["/aprender", "lembra disso", "guarda essa preferência"]
---

Use para registrar apenas preferências de estilo, fluxo, defaults ou aliases. O arquivo real é
`.claude/memory.local/instincts.local.md`, local e gitignored.

1. Resuma a preferência detectada em uma linha no formato:
   `- [id-curto] QUANDO <gatilho> ENTÃO <comportamento> (aprovado AAAA-MM-DD)`.
2. Verifique o texto: se houver nome, CPF, OAB, e-mail, telefone, processo real ou outro dado
   pessoal, recuse gravar e explique que preferências devem ser generalizadas e PII-free.
3. Mostre a linha proposta e pergunte: “Quer que eu guarde esta preferência? Responda sim.”
4. Só depois de receber exatamente `sim`, crie o arquivo se necessário e faça append da linha.
   Nunca reescreva instintos existentes.
5. Confirme o id salvo, sem repetir dados pessoais.
