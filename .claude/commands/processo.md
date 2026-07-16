---
name: processo
description: Consulta status e movimentações de processo em qualquer TJ
triggers: ["/processo", "status do processo", "movimentações do processo", "consultar processo"]
---

## Proveniência obrigatória
Na saída, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Movimentação ou
dado extraído do texto recebe `[documento do usuário]`; prazo calculado pelo CLI recebe
`[motor determinístico]`; e regra ou tese não conferida recebe
`[conhecimento do modelo — conferir]`. Uma etiqueta geral não basta.

Consulte o processo: $ARGUMENTS

## Fluxo
1. Extrair número CNJ do input (formato: NNNNNNN-DD.AAAA.J.TT.OOOO)
2. Pedir/colar o texto da intimação, movimentação ou página raspada do tribunal. O parser atual aceita texto colado/scraped; não há consulta online determinística nesta skill.
3. Detectar tribunal pelo texto e, se disponível, pelo remetente:
```bash
uv run legalops tribunal-detect --input "[arquivo-texto]" --sender "[remetente-opcional]"
```
4. Extrair dados processuais do texto:
```bash
uv run legalops parse --input "[arquivo-texto]"
```
5. Se houver prazo extraído, calcular com `legalops prazo --data-publicacao AAAA-MM-DD --prazo-dias N --parte [particular|fazenda|mp|defensoria] --tribunal TJPR --hoje AAAA-MM-DD`.

## Apresentação
```
DRAFT — Requer revisão e assinatura

📋 Processo [CNJ mascarado]
Tribunal: [TJXX] [documento do usuário]
Partes: [mascarado — ex: "Autor vs. Réu"]
Última movimentação: DD/MM/AAAA — [tipo] [documento do usuário]

📜 Histórico recente:
  • [data] — [tipo de movimentação extraída do texto]
  • [data] — [tipo de movimentação extraída do texto]
  ...

⏰ Prazos extraídos desta movimentação: [dado do texto] [documento do usuário]
⏰ Data final calculada: [se houver] [motor determinístico]
```

## Guardrails
- Sempre mascarar número CNJ completo no output (exibir apenas últimos 6 dígitos)
- Partes: exibir como "Parte A" / "Parte B" — nunca nome real em log
- Intimações detectadas → calcular prazo automaticamente via skill `/prazo`
- Nenhuma citação ou movimentação colada deve ser tratada como verdade sem conferência no tribunal/fonte primária

## TJs suportados
TJPR · TJSP · TJMG · TJSC · TJRJ · TJDFT
Para outros: "TJ não suportado ainda — consulte diretamente no site do tribunal."
