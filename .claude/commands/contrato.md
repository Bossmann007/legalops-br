---
name: contrato
description: Analisa contrato — red flags, cláusulas problemáticas, sugestões
triggers: ["/contrato", "analisar contrato", "revisar contrato", "red flags no contrato"]
---

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
[Tipo de contrato identificado]
[Partes: pseudônimos]

🔴 Red Flags (N encontrados):
  • [cláusula X] — [problema] — [sugestão]

🟡 Pontos de Atenção:
  • [cláusula Y] — [observação]

🟢 Cláusulas Adequadas:
  • [lista breve]

📅 Datas Importantes:
  • Vigência: [data início] → [data fim]
  • Renovação automática: [sim/não — aviso com N dias de antecedência]
  • Rescisão: [prazo de aviso]

💡 Sugestões:
  1. [sugestão concreta]
  2. [sugestão concreta]

DRAFT — Esta análise requer validação do advogado responsável.
```

## Após análise
Perguntar: "Deseja registrar data de renovação para alertas automáticos?"
Se sim: orientar a advogada a adicionar alias opaco em `data/contratos.json` (gitignored) e validar com `uv run legalops renovacao --hoje AAAA-MM-DD`.
