---
name: bancario-contrato
description: Checklist de triagem de contrato bancario/financeiro sem teses juridicas
triggers: ["/bancario-contrato", "contrato bancario", "contrato financeiro", "fraude bancaria", "perda com investimento"]
---

Use para leitura inicial de contrato bancario, financiamento, investimento, portabilidade, contestacao de tarifa ou caso de fraude bancaria. A skill organiza fatos e red flags para revisao da advogada. Nao importar teses, sumulas, artigos ou conclusoes da fonte sem verificacao humana.

## Guardrails
- Toda saida juridica deve comecar com `DRAFT — Requer revisão e assinatura`.
- Nao afirmar abusividade, ilegalidade, nulidade, prazo ou entendimento jurisprudencial.
- Qualquer referencia legal, sumula, regra BCB/CVM ou tese deve ir como `verificar na fonte primaria`.
- Usar aliases de cliente (`CLI-XXX`) e mascarar conta, CPF, processo, telefone, e-mail e valores sensiveis quando possivel.
- Em fraude, preservar cronologia e evidencias sem orientar destruicao/alteracao de documentos.

## Intake
1. Tipo de caso: contrato bancario, investimento, fraude, boleto, portabilidade, cartao, consignado, mercado de capitais, outro.
2. Cliente: alias e perfil geral, sem nome real.
3. Instituicao/contraparte: alias ou nome se for pessoa juridica publica no documento.
4. Documento recebido: contrato, extrato, comprovante, conversa, contestacao administrativa, B.O., resposta do banco/CVM/BCB.
5. Datas-chave: contratacao, evento, contestacao, resposta, prejuizo percebido.
6. Valores: usar faixas ou valores redigidos se nao forem necessarios.
7. Objetivo: recuperar valor, contestar clausula, preparar notificacao, reunir prova, avaliar risco.

## Checklist de leitura
| Tema | Perguntas | Evidencia |
|---|---|---|
| Identificacao | partes, produto, conta/contrato, canal de contratacao | contrato/extrato |
| Consentimento/autorizacao | cliente autorizou? ha autenticacao, assinatura, token, gravacao? | logs/comprovantes |
| Informacao pre-contratual | taxas, custos, riscos, prazos e encargos estavam claros? | proposta/termo |
| Custos e encargos | juros, tarifas, CET, multa, IOF, custo total aparecem? | clausulas/tabelas |
| Portabilidade | houve pedido? origem/destino? autorizacao? | protocolo |
| Investimento | perfil de risco, suitability, produto, liquidez, perda, material de oferta | ficha/carteira |
| Fraude | vetor: falso funcionario, boleto, clonagem, engenharia social, SIM swap, Pix | cronologia |
| Contestacao | prazos internos, protocolos, resposta da instituicao | e-mails/protocolos |
| Provas | documentos faltantes, screenshots, extratos, B.O., atendimento | lista |

## Output
```markdown
DRAFT — Requer revisão e assinatura

# Triagem Bancaria/Financeira — [CLI-XXX]

## Nota da revisora
- Documento lido: [tipo / paginas / parcial]
- Dados pessoais: [redigidos / pendente]
- Regras/tese a verificar em fonte primaria: [lista]

## Resumo factual
[Cronologia curta, sem conclusao juridica.]

## Red flags de triagem
| Severidade | Tema | Fato observado | Evidencia | Pergunta para revisao |
|---|---|---|---|---|

## Documentos faltantes
- [ ] contrato/proposta integral
- [ ] extratos/comprovantes
- [ ] protocolos de atendimento
- [ ] comunicacoes com banco/corretora
- [ ] material de oferta/suitability, se investimento
- [ ] boletim de ocorrencia, se fraude

## Proximas opcoes
1. Preparar pergunta/document request para o cliente.
2. Preparar notificacao extrajudicial DRAFT.
3. Montar timeline probatoria.
4. Encaminhar para pesquisa juridica com fontes primarias.
```
