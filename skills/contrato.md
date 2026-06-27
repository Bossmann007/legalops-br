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
echo "[texto]" | uv run legalops redact --output texto_redacted.txt
```
3. Analisar:
```bash
uv run legalops contrato --analisar --input texto_redacted.txt
```

## Output Obrigatório
```
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
Se sim: `uv run legalops renovacao --registrar --contrato "[id]" --data-renovacao "[data]"`
