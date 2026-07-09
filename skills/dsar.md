---
name: dsar
description: Processa solicitação LGPD (acesso, correção, exclusão, portabilidade)
triggers: ["/dsar", "solicitação LGPD", "titular de dados", "pedido de exclusão"]
---

## Prazo Legal
Usar **15 dias** como SLA interno inicial do harness, salvo orientação da advogada. Antes de enviar resposta ao titular, confirmar o prazo e a regra aplicável em fonte primária.

## Fluxo
1. Antes de colar a solicitação:
   - Redigir anexos, documentos pessoais e trechos irrelevantes.
   - Confirmar que o pedido será salvo apenas com alias (`TIT-XXX` / `CLI-XXX`).
   - Se houver processo, litígio, jornalista, regulador em cópia ou pedido incomum, escalar para a advogada antes de responder.

2. Coletar dados da solicitação:
   - Tipo: acesso / correção / exclusão / portabilidade / oposição
   - Titular: pseudônimo interno (nunca logar nome real)
   - Data de recebimento
   - Canal: email / WhatsApp / presencial
   - Identidade: verificada / pendente / não verificada
   - Escopo entendido: uma frase sobre o que a pessoa está pedindo

3. Registrar:
```bash
uv run legalops dsar --registrar \
  --tipo [acesso|correcao|exclusao|portabilidade|oposicao] \
  --titular CLI-XXX \
  --data-recebimento AAAA-MM-DD
```

4. Enviar ou preparar confirmação de recebimento (DRAFT):
   - Confirmar data de recebimento.
   - Repetir o pedido entendido.
   - Informar que a identidade será verificada quando necessário.
   - Não entregar dados nesta primeira mensagem.

5. Verificar identidade:
   - Pedido vindo de canal autenticado: registrar evidência.
   - Pedido por email/WhatsApp: confirmar que bate com cadastro ou pedir etapa adicional.
   - Pedido de exclusão/portabilidade ou dados sensíveis: usar verificação reforçada.
   - Se não verificar, preparar resposta pedindo validação sem expor dados.

6. Processar (buscar dados do titular no sistema):
```bash
uv run legalops dsar --processar --id [DSAR-ID]
```

7. Caminhar sistema a sistema:
   - Banco principal / CRM / planilha
   - Email e WhatsApp corporativo
   - Contratos e documentos
   - Logs e auditoria
   - Backups
   - Fornecedores/operadores

8. Avaliar retenções e exceções:
   - Nunca afirmar exceção legal sem revisão da advogada e fonte primária.
   - Separar dado do titular de dado de terceiros.
   - Registrar o que será entregue, corrigido, excluído, retido ou negado.

9. Gerar resposta substantiva:
```bash
uv run legalops dsar --gerar-resposta --id [DSAR-ID]
```

## Output Esperado
```
DRAFT — Requer revisão e assinatura

📋 DSAR-[ID] — [tipo]
Titular: [CLI-XXX]
Recebido: DD/MM/AAAA
SLA interno de resposta: DD/MM/AAAA (confirmar prazo aplicável em fonte primária)
Dias restantes: N
Identidade: [verificada/pendente/não verificada]

Dados localizados: [sim/não/parcial]
Sistemas verificados: [lista]
Retenções/exceções propostas: [nenhuma/lista — requer revisão]
Resposta gerada: [path do documento]
```

## Guardrails
- Nunca logar nome real do titular — apenas alias interno
- Resposta ao titular sempre via canal seguro (nunca WhatsApp público)
- Exclusão: documentar tratamento de backups e trilha de auditoria quando aplicável
- Negativas, retenções e exceções: só com revisão da advogada e fonte primária
- Produzir duas peças quando cabível: confirmação de recebimento e resposta substantiva
- Não enviar resposta diretamente; humano revisa, assina e envia
