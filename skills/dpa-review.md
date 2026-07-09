---
name: dpa-review
description: Revisao de DPA/contrato de tratamento de dados para clientes o escritório cliente
triggers: ["/dpa-review", "revisar DPA", "contrato de tratamento", "acordo de tratamento de dados"]
---

Use para revisar contrato, anexo ou clausula de tratamento de dados. A skill separa revisao quando o cliente atua como controlador, operador ou papel indefinido. Se o papel estiver duvidoso, pare e pergunte.

## Guardrails
- Toda saida juridica deve comecar com `DRAFT — Requer revisão e assinatura`.
- Nao assinar, aprovar ou devolver redline como final sem revisao da advogada.
- Nao tratar prazo, transferencia internacional, incidente, base legal ou regra setorial como verdade sem `verificar na fonte primaria`.
- Redigir PII antes de salvar trechos do contrato ou exemplos.
- Se envolver dados de saude, financeiros, criancas/adolescentes, biometria, IA ou transferencia internacional, marcar revisao humana obrigatoria.

## Primeiro passo: direcao
Classifique:
- Cliente da o escritório cliente como `controlador`: revisao de fornecedor/operador.
- Cliente da o escritório cliente como `operador`: revisao de DPA enviado por cliente/controlador.
- `indefinido`: papel contratual nao bate com a operacao ou faltam fatos.

Se `indefinido`, nao force conclusao. Liste perguntas para a advogada/cliente.

## Checklist termo a termo
| Tema | O que verificar | Sinal de alerta |
|---|---|---|
| Papeis | controlador, operador, controlador conjunto, suboperador | papel formal incompatível com a realidade |
| Escopo | finalidades e instrucoes documentadas | expressoes amplas como "finalidades correlatas" |
| Dados | categorias e titulares | dados sensiveis sem tratamento diferenciado |
| Suboperadores | lista, troca, notificacao, veto | fornecedor pode trocar sem informar |
| Segurança | controles concretos, auditoria, segregacao | promessa generica sem anexo |
| Incidente | gatilho, fluxo, contato, evidencia | prazo/forma ausente ou dependente de criterio unilateral |
| Direitos dos titulares | apoio a acesso, correcao, exclusao, portabilidade | contrato empurra tudo para parte errada |
| Retencao e descarte | devolucao, eliminacao, backup | dados vivem por prazo indefinido |
| Transferencia internacional | pais, mecanismo, fornecedor | corredor internacional sem mecanismo documentado |
| Responsabilidade | limite, indenidade, excecoes | responsabilidade ilimitada ou isencao total |
| Uso secundario | analytics, treinamento de IA, marketing, melhoria de servico | uso proprio do fornecedor sem autorizacao clara |

## Output
```markdown
DRAFT — Requer revisão e assinatura

# Revisao DPA — [CLI-XXX] x [FOR/CTR-XXX]

## Nota da revisora
- Direcao: [cliente controlador / cliente operador / indefinida]
- Fontes: [contrato completo / clausulas / relato]
- Dados pessoais: [redigidos / nao recebidos / pendente]
- Itens a verificar em fonte primaria: [lista]

## Bottom line
[2-3 frases: pode seguir para negociacao? quais blockers?]

## Issues por severidade
| Severidade | Clausula/tema | Problema | Risco pratico | Redline/pergunta sugerida |
|---|---|---|---|---|

## Consistencia com politica e RIPD
| Documento | Conflito aparente | Acao |
|---|---|---|

## Redlines sugeridas
[Editar no menor nivel possivel: palavra, frase, subclausula. Se substituir clausula inteira, explicar por que.]

## Se a contraparte nao aceitar
| Issue | Fallback possivel | Quem decide |
|---|---|---|

## Antes de assinar
- [ ] Papel das partes confirmado.
- [ ] Transferencia internacional verificada.
- [ ] Regra setorial aplicavel verificada.
- [ ] Advogada revisou e autorizou envio/assinatura.
```
