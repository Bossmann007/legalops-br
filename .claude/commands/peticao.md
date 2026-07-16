---
name: peticao
description: Rascunho de petição (contestação, recurso, inicial, embargos)
triggers: ["/peticao", "rascunho de petição", "redigir petição", "draft de petição"]
---

## Proveniência obrigatória
Na peça, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Fatos e teses
fornecidos pela advogada recebem `[documento do usuário]`; fundamento criado ou lembrado pelo
modelo recebe `[conhecimento do modelo — conferir]`; e `[fonte primária]` só vale se a fonte
oficial foi realmente consultada nesta sessão. Uma etiqueta geral não basta.

## Instruções

**IMPORTANTE:** Todo output desta skill é DRAFT. O advogado revisa e assina.

## Coleta de Informações
Pergunte em sequência:
1. **Tipo de peça:** contestação / recurso de apelação / recurso inominado / inicial / embargos de declaração / agravo / outro
2. **Fatos resumidos:** o que aconteceu? (cliente cola ou descreve)
3. **Tese principal:** qual o argumento central?
4. **Pedido:** o que quer ao final?
5. **Tribunal/vara:** para adequar linguagem e formato

## Redação
Use Claude para gerar o rascunho com:
- Cabeçalho formal (Excelentíssimo Senhor Doutor Juiz / Colendo Tribunal)
- Qualificação das partes (pseudônimos — NUNCA nome real aqui)
- Dos Fatos (numerados; cada fato com `[documento do usuário]`)
- Do Direito (cada fundamento legal com a etiqueta de proveniência correta)
- Dos Pedidos (numerados, concretos)
- Encerramento formal

## Output
```
DRAFT — Requer revisão, ajuste e assinatura do Dr./Dra. [advogado]
Gerado em: [data/hora]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PEÇA GERADA AQUI]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Verificar antes de protocolar:
□ Qualificação das partes (nome real, CPF/CNPJ)
□ Número do processo
□ Assinatura digital do advogado
□ Recolhimento de custas (se aplicável)
□ Prazo de protocolo
```

## Guardrails
- NUNCA incluir dados reais de cliente no draft (usar [CLIENTE], [RÉPLICANTE], etc.)
- NUNCA afirmar certeza jurídica — usar "entende-se", "sustenta-se"
- Fundamentação legal: verificar atualização das normas citadas
