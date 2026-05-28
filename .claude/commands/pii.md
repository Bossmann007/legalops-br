---
description: "Verifica e redacta PII em texto jurídico para uso seguro em dev/test"
---

Analise e redacte PII no seguinte texto: $ARGUMENTS

PII a identificar e redactar (LGPD Art. 5 + dados jurídicos BR):
- CPF: substituir por CPF_FAKE_XXX
- RG: substituir por RG_FAKE_XXX
- Nome completo: substituir por NOME_FAKE_XXX
- Endereço: substituir por ENDERECO_FAKE_XXX
- Número de processo: MANTER (não é PII — é dado público)
- Data de nascimento: substituir por DOB_FAKE_XXX
- Telefone/email: substituir por CONTATO_FAKE_XXX

Output:
1. Texto redactado (pronto para usar em test)
2. Mapa de substituições feitas
3. Aviso se algum campo ambíguo foi encontrado
