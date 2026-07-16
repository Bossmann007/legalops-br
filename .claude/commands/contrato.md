---
name: contrato
description: Analisa contrato — red flags, cláusulas problemáticas, sugestões
triggers: ["/contrato", "analisar contrato", "revisar contrato", "red flags no contrato"]
---

## Proveniência obrigatória
Na saída, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Texto da
cláusula e fatos do contrato recebem `[documento do usuário]`; avaliação, risco ou sugestão
jurídica não conferida recebe `[conhecimento do modelo — conferir]`; e `[fonte primária]` só
vale se a fonte oficial foi realmente consultada nesta sessão. Uma etiqueta geral não basta.

Analise o contrato: $ARGUMENTS

## Fluxo
1. Se contrato não foi colado: pedir o texto ou caminho do arquivo
2. Redactar PII antes de processar:
```bash
uv run legalops redact --input "[arquivo-original]" > texto_redacted.txt
```
3. Analisar:
```bash
uv run legalops contract --input texto_redacted.txt --skip-redact
```

## Output Obrigatório
```
DRAFT — Requer revisão e assinatura

📄 Análise de Contrato
[Tipo de contrato identificado] [documento do usuário]
[Partes: pseudônimos]

🔴 Red Flags (N encontrados):
  • [cláusula X] [documento do usuário] — [problema] [conhecimento do modelo — conferir]
    — [sugestão] [conhecimento do modelo — conferir]

🟡 Pontos de Atenção:
  • [cláusula Y] [documento do usuário] — [observação]
    [conhecimento do modelo — conferir]

🟢 Cláusulas Adequadas:
  • [cláusula] [documento do usuário] — [avaliação]
    [conhecimento do modelo — conferir]

📅 Datas Importantes:
  • Vigência: [data início] → [data fim] [documento do usuário]
  • Renovação automática: [sim/não — aviso com N dias de antecedência] [documento do usuário]
  • Rescisão: [prazo de aviso] [documento do usuário]

💡 Sugestões:
  1. [sugestão concreta] [conhecimento do modelo — conferir]
  2. [sugestão concreta] [conhecimento do modelo — conferir]

DRAFT — Esta análise requer validação do advogado responsável.
```

## Após análise
Perguntar: "Deseja registrar data de renovação para alertas automáticos?"
Se sim: orientar a advogada a adicionar alias opaco em `data/contratos.json` (gitignored) e validar com `uv run legalops renovacao --hoje AAAA-MM-DD`.
