---
name: prazo
description: Calcula prazo processual CPC com feriados nacionais e estaduais
triggers: ["/prazo", "calcular prazo", "quando vence", "prazo para"]
---

Calcule o prazo para: $ARGUMENTS

## Regras CPC Obrigatórias
1. **Art. 219**: contar apenas dias úteis (seg–sex, exceto feriados)
2. **Art. 224**: prazo começa no dia útil seguinte à intimação
3. **Art. 229**: intimação via sistema eletrônico → +1 dia útil
4. **Prazo em dobro** (Art. 183/186/128): Fazenda Pública, MP, Defensoria

## Fluxo
1. Se data de intimação não fornecida: perguntar antes de calcular
2. Identificar tipo de ato (contestação, recurso, manifestação, etc.)
3. Executar:
```bash
uv run legalops prazo --intimacao "[data]" --tipo "[tipo]" --partes "[partes]"
```
4. Se o CLI não tiver os parâmetros, calcular com as regras acima e feriados de:
   - Nacional: `~/Projects/legalops-br/src/legalops/cpc_prazos.py` (lista interna)
   - Estadual: perguntar o estado do tribunal

## Formato de Resposta
```
📅 Cálculo de Prazo

Data da intimação: DD/MM/AAAA
Tipo: [contestação/recurso/etc]
Prazo base: N dias úteis
Em dobro? [Sim — Fazenda Pública / Não]
Feriados no período: [lista ou "nenhum"]

⚖️ Data final: **DD/MM/AAAA**

⚠️ Alertas automáticos configurados: D-3 e D-1
```

Após calcular, perguntar: "Deseja registrar esse prazo no sistema para alertas automáticos?"
Se sim: `uv run legalops prazo --registrar --data-final "[data]" --descricao "[desc]"`
