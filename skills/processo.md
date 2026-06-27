---
name: processo
description: Consulta status e movimentações de processo em qualquer TJ
triggers: ["/processo", "status do processo", "movimentações do processo", "consultar processo"]
---

Consulte o processo: $ARGUMENTS

## Fluxo
1. Extrair número CNJ do input (formato: NNNNNNN-DD.AAAA.J.TT.OOOO)
2. Detectar tribunal:
```bash
uv run legalops tribunal-detect --numero "[cnj]"
```
3. Consultar movimentações:
```bash
uv run legalops processo --numero "[cnj]" --movimentacoes --ultimas 10
```

## Apresentação
```
📋 Processo [CNJ mascarado]
Tribunal: [TJXX]
Partes: [mascarado — ex: "Autor vs. Réu"]
Última movimentação: DD/MM/AAAA — [tipo]

📜 Histórico recente:
  • [data] — [tipo de movimentação]
  • [data] — [tipo de movimentação]
  ...

⏰ Prazos extraídos desta movimentação: [se houver — calcular automaticamente]
```

## Guardrails
- Sempre mascarar número CNJ completo no output (exibir apenas últimos 6 dígitos)
- Partes: exibir como "Parte A" / "Parte B" — nunca nome real em log
- Intimações detectadas → calcular prazo automaticamente via skill `/prazo`

## TJs suportados
TJPR · TJSP · TJMG · TJSC · TJRJ · TJDFT
Para outros: "TJ não suportado ainda — consulte diretamente no site do tribunal."
