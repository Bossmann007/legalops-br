---
name: dsar
description: Processa solicitação LGPD (acesso, correção, exclusão, portabilidade)
triggers: ["/dsar", "solicitação LGPD", "titular de dados", "pedido de exclusão"]
---

## Prazo Legal
**15 dias** para responder (LGPD Art. 18 + ANPD Resolução CD/ANPD nº 2/2022).

## Fluxo
1. Coletar dados da solicitação:
   - Tipo: acesso / correção / exclusão / portabilidade / oposição
   - Titular: pseudônimo interno (nunca logar nome real)
   - Data de recebimento
   - Canal: email / WhatsApp / presencial

2. Registrar:
```bash
uv run legalops dsar --registrar \
  --tipo [acesso|correcao|exclusao|portabilidade|oposicao] \
  --titular CLI-XXX \
  --data-recebimento AAAA-MM-DD
```

3. Processar (buscar dados do titular no sistema):
```bash
uv run legalops dsar --processar --id [DSAR-ID]
```

4. Gerar resposta:
```bash
uv run legalops dsar --gerar-resposta --id [DSAR-ID]
```

## Output Esperado
```
📋 DSAR-[ID] — [tipo]
Titular: [CLI-XXX]
Recebido: DD/MM/AAAA
Prazo de resposta: DD/MM/AAAA (15 dias)
Dias restantes: N

Dados localizados: [sim/não/parcial]
Resposta gerada: [path do documento]

DRAFT — Requer revisão e assinatura do DPO/responsável
```

## Guardrails
- Nunca logar nome real do titular — apenas alias interno
- Resposta ao titular sempre via canal seguro (nunca WhatsApp público)
- Exclusão: confirmar backup destruído (audit trail obrigatório)
- Negativas: fundamentar em bases legais (legítimo interesse, obrigação legal, etc.)
