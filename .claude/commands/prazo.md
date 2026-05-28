---
description: "Calcula prazo CPC para um ato processual"
---

Calcule o prazo para: $ARGUMENTS

Regras CPC obrigatórias:
1. Art. 219: contar apenas dias úteis (seg-sex, exceto feriados nacionais)
2. Art. 224: prazo começa no dia útil seguinte à intimação
3. Art. 229: intimação via sistema eletrônico — prazo +1 dia útil
4. Verificar se há prazo em dobro (Fazenda Pública, MP, Defensoria — Art. 183/186/128)

Formato de resposta:
- Data da intimação: [extrair do input]
- Tipo de prazo: [contestação/recurso/etc]
- Prazo base (dias úteis): [N dias]
- Prazo em dobro? [sim/não — motivo]
- Data final: **DD/MM/AAAA**
- Feriados considerados no período: [lista ou "nenhum"]

Se data de intimação não fornecida, perguntar antes de calcular.
