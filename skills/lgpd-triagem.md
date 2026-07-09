---
name: lgpd-triagem
description: Triagem rapida PROCEED / PIA / STOP para atividade de tratamento de dados
triggers: ["/lgpd-triagem", "triagem LGPD", "precisa de RIPD", "pode tratar esses dados", "privacy check"]
---

Use esta skill antes de iniciar uma atividade de tratamento, revisar uma feature, contratar fornecedor ou responder a uma ideia de cliente PME. O objetivo e decidir o proximo passo, nao dar parecer final.

## Guardrails
- Toda saida juridica deve comecar com `DRAFT — Requer revisão e assinatura`.
- `PROCEED` e classificacao PRELIMINAR de LLM — NUNCA e "aprovado" nem deve ser citado a
  cliente como liberacao. Terminar SEMPRE com "Fora do escopo desta triagem" (o que nao foi
  avaliado e exige RIPD/parecer). A triagem prioriza, nao decide.
- Classificacoes sao preliminares e dependem de revisao humana.
- Nao afirmar artigo, prazo, sancao ou requisito regulatorio sem marcar `verificar na fonte primaria`.
- Se houver dado real de titular, redigir ou substituir por alias antes da analise.

## Classificacoes
- `PROCEED`: nao apareceu bloqueio evidente; manter salvaguardas padrao e registrar justificativa.
- `PIA`: precisa de RIPD/avaliacao de impacto ou analise aprofundada antes de prosseguir.
- `STOP`: ha conflito aparente com politica, falta de base factual, uso inesperado de dado sensivel, ou risco que precisa ser redesenhado antes de seguir.

## Perguntas minimas
1. Qual e a atividade? O que muda para o titular?
2. Quais dados entram, saem ou sao derivados?
3. Quem sao os titulares?
4. Qual e a finalidade de negocio?
5. Ha fornecedor, IA, automacao, marketing, transferencia internacional ou blockchain?
6. A politica de privacidade atual cobre essa finalidade?
7. O titular esperaria esse uso?
8. Existe forma de atender o objetivo com menos dados?

## Indicadores de PIA
Marcar `PIA` quando houver qualquer sinal abaixo:
- dados de saude, financeiros, biometria, menores, geolocalizacao precisa ou outro dado de alta exposicao;
- decisao automatizada ou perfilamento que afete pessoa;
- compartilhamento com fornecedor novo ou uso por terceiro;
- mudanca de finalidade de dados ja coletados;
- retencao longa sem justificativa documentada;
- uso que o titular provavelmente nao espera;
- conflito ou silencio na politica de privacidade.

## Indicadores de STOP
Marcar `STOP` quando:
- a finalidade nao esta clara;
- nao ha documento, politica ou contrato suficiente para avaliar;
- o cliente quer enviar dados reais sem redacao/controle;
- a atividade parece contrariar promessa feita ao titular;
- ha pedido de "liberar" uso sensivel sem revisao da advogada;
- a resposta depender de norma, tese ou prazo ainda nao verificado.

## Output
```markdown
DRAFT — Requer revisão e assinatura

# Triagem LGPD — [atividade]

## Nota da revisora
- Fontes: [documentos / relato do cliente / pendente]
- Dados pessoais: [redigidos / nao recebidos / pendente]
- Itens a verificar em fonte primaria: [lista]

## Classificacao
**Resultado:** [PROCEED / PIA / STOP]
**Motivo em uma frase:** [explicacao curta]

## Fatos usados
| Pergunta | Resposta | Lacuna |
|---|---|---|

## Condicoes antes de prosseguir
| Condicao | Dono | Status |
|---|---|---|

## Proximo passo
- Se `PROCEED`: registrar justificativa e revisar periodicamente.
- Se `PIA`: rodar `/ripd` com os fatos ja coletados.
- Se `STOP`: pedir documentos, redesenhar fluxo ou levar decisao para a advogada.
```
