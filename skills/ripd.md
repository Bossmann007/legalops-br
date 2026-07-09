---
name: ripd
description: Rascunho de Relatorio de Impacto a Protecao de Dados para clientes o escritório cliente
triggers: ["/ripd", "RIPD", "relatorio de impacto", "PIA", "DPIA"]
---

Use para documentar uma avaliacao de impacto de privacidade. O arquivo produzido e rascunho interno para revisao da advogada, nao documento para envio automatico a regulador, cliente ou contraparte.

## Guardrails
- Toda saida juridica deve comecar com `DRAFT — Requer revisão e assinatura`.
- Nao afirmar obrigatoriedade legal do RIPD, base legal, prazo ou requisito sem marcar `verificar na fonte primaria`.
- Nao enviar RIPD a regulador, cliente, fornecedor ou titular sem aprovacao expressa da advogada.
- Dados de titulares devem estar redigidos ou substituidos por aliases.
- Carregar resultado de `/lgpd-triagem`, se existir, e manter severidade igual ou superior salvo justificativa expressa.

## Intake
Colete:
1. atividade/produto/processo avaliado;
2. categorias de dados e titulares;
3. finalidade e beneficio esperado;
4. sistemas, fornecedores, acesso interno, armazenamento e retencao;
5. politica de privacidade ou contrato aplicavel;
6. riscos de vazamento, discriminacao, surpresa do titular, reidentificacao, uso indevido por fornecedor;
7. controles existentes e controles planejados.

## Qualidade dos riscos
Riscos devem ser especificos. Evite "descumprimento da LGPD" ou "vazamento" como frase solta. Prefira: "planilha com dados financeiros acessivel por equipe nao envolvida no caso, sem trilha de auditoria".

## Output
```markdown
DRAFT — Requer revisão e assinatura

# RIPD — [CLI-XXX] — [atividade]

## Nota da revisora
- Fontes: [documentos lidos / relatos / pendencias]
- Triage anterior: [PROCEED / PIA / STOP / nao localizado]
- Itens a verificar em fonte primaria: [lista]
- Decisoes juridicas pendentes: [lista]

## 1. Sumario executivo
[O que e a atividade, por que existe, risco geral e recomendacao preliminar.]

**Risco geral preliminar:** [baixo / medio / alto / muito alto]
**Recomendacao preliminar:** [prosseguir / prosseguir com condicoes / redesenhar / suspender]

## 2. Descricao do tratamento
| Campo | Resposta |
|---|---|
| Atividade | |
| Titulares | |
| Categorias de dados | |
| Finalidades | |
| Dados novos ou reaproveitados | |

## 3. Fluxo de dados
| Etapa | Sistema/local | Quem acessa | Terceiros | Retencao | Lacunas |
|---|---|---|---|---|---|

## 4. Base e compatibilidade
| Finalidade | Base indicada pelo cliente | Conflito aparente | Verificacao pendente |
|---|---|---|---|

## 5. Consistencia com politica/contrato
| Compromisso/documento | Consistente? | Observacao |
|---|---|---|

## 6. Riscos e mitigacoes
| # | Risco especifico | Probabilidade | Impacto | Mitigacao | Dono | Status |
|---|---|---|---|---|---|---|

## 7. Direitos do titular
| Direito/processo | Como atender | Lacuna |
|---|---|---|

## 8. Condicoes antes de seguir
- [ ] [condicao concreta]

## 9. Assinatura e revisao
**Responsavel interno:** [preencher]
**Revisora juridica:** [preencher]
**Data de revisao:** [preencher]
```

## Limites
- Nao calcula risco juridico final.
- Nao substitui validacao de norma atual.
- Nao redige politica publica; se houver gap de politica, abrir tarefa separada.
