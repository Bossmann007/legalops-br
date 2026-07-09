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
3. Executar (subcomando determinístico do engine):
```bash
uv run legalops prazo \
  --data-publicacao AAAA-MM-DD \
  --prazo-dias N \
  --parte [particular|fazenda|mp|defensoria] \
  --tribunal TJPR \
  --hoje AAAA-MM-DD
# --via-dje  → some se a intimação foi pelo Diário eletrônico (Art. 229)
```
O comando retorna JSON com `data_final`, dias corridos e flags de dobro/recesso aplicados.
Se faltar dado (data de publicação, nº de dias, tribunal), pergunte antes de calcular.

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

Após calcular, avise: o cálculo é rede de segurança — **confira o prazo no PJe/Projudi**, que é
a fonte oficial. Para acompanhar prazos recorrentes, anote-os no controle oficial do tribunal;
o engine não persiste prazos (não há registro/alerta automático nesta versão).
