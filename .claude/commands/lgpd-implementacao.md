---
name: lgpd-implementacao
description: Plano de adequacao LGPD para PMEs atendidas pela o escritório cliente
triggers: ["/lgpd-implementacao", "implementar LGPD", "plano LGPD", "adequacao LGPD"]
---

## Proveniência obrigatória
Na saída, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Fato ou
compromisso extraído dos materiais recebe `[documento do usuário]`; recomendação ou regra não
conferida recebe `[conhecimento do modelo — conferir]`; e `[fonte primária]` só vale se a fonte
oficial foi realmente consultada nesta sessão. Uma etiqueta geral não basta.

Use esta skill para estruturar um programa de privacidade para PME cliente da o escritório cliente. A saida e operacional: mapa de dados, lacunas, responsaveis e plano faseado. Nao afirmar conclusao juridica final.

## Guardrails
- Toda saida juridica deve comecar com `DRAFT — Requer revisão e assinatura`.
- Antes de citar lei, artigo, resolucao, prazo, sancao ou entendimento da ANPD, marcar como `verificar na fonte primaria`.
- Nao usar dados reais de titulares ou clientes em exemplos; usar aliases `CLI-XXX`, `TIT-XXX`, `FOR-XXX`.
- Se o material contiver dados pessoais, redigir antes de registrar em nota, log ou arquivo.
- Se a empresa tratar dados financeiros, de saude, criancas/adolescentes, biometria ou dados de alta exposicao, elevar para revisao humana.

## Intake
Colete somente o necessario para montar o plano:

1. Empresa: setor, porte, canais digitais, principais servicos.
2. Titulares: clientes, leads, pacientes, usuarios, colaboradores, fornecedores.
3. Dados tratados: categorias, origem, finalidade, sistemas, terceiros, retencao.
4. Riscos especiais: dados financeiros, dados de saude, decisao automatizada, marketing, transferencia internacional, blockchain/ativos digitais.
5. Governanca: responsavel interno, encarregado/DPO, fornecedores criticos, politica de privacidade existente.
6. Documentos disponiveis: politica de privacidade, contratos com fornecedores, formulario de consentimento, planilha de sistemas, historico de incidentes.

## Fluxo
1. Confirmar se ha material suficiente. Se faltar base factual, pedir os documentos ou marcar lacuna.
2. Montar matriz de atividades de tratamento.
3. Classificar lacunas por severidade operacional: `bloqueante`, `alta`, `media`, `baixa`.
4. Separar o que e documento, processo, treinamento, contrato, seguranca e resposta a incidente.
5. Indicar itens que exigem validacao juridica ou fonte primaria.
6. Fechar com plano de 30/60/90 dias.

## Output
```markdown
DRAFT — Requer revisão e assinatura

# Plano de Adequacao LGPD — [CLI-XXX]

## Nota da revisora
- Fontes: [documentos lidos / informacoes fornecidas / itens a verificar em fonte primaria]
- Dados pessoais: [redigidos / nao recebidos / pendente redacao]
- Pontos para decisao juridica: [N]

## Sumario executivo
[2-4 frases em linguagem de negocio, sem parecer final.]

## Mapa de tratamento
| Atividade | Dados | Titulares | Finalidade | Sistema | Terceiros | Retencao | Lacunas |
|---|---|---|---|---|---|---|---|

## Lacunas priorizadas
| Severidade | Lacuna | Evidencia | Risco pratico | Acao recomendada | Responsavel |
|---|---|---|---|---|---|

## Documentos a preparar ou revisar
- Politica de privacidade
- Aviso de cookies/marketing, se aplicavel
- Registro de atividades
- Modelo de DPA/contrato de tratamento
- Procedimento de atendimento a titulares
- Plano de resposta a incidente
- Politica de retencao e descarte

## Plano 30/60/90
| Prazo | Acoes | Dono | Evidencia de conclusao |
|---|---|---|---|

## Verificacoes obrigatorias antes de confiar
- Confirmar bases legais e prazos em fonte primaria.
- Confirmar se ha regra setorial aplicavel ao setor do cliente.
- Validar contrato/DPA antes de assinar ou enviar a terceiro.
```

## Limites
- Nao aprova conformidade.
- Nao substitui RIPD quando houver atividade de maior risco.
- Nao decide base legal em caso duvidoso; marca para revisao da advogada.
