---
name: saude-privacidade
description: Plano de privacidade para clinicas, hospitais e consultoria em direito da saude
triggers: ["/saude-privacidade", "privacidade em saude", "LGPD saude", "risco medico hospitalar"]
---

Use para estruturar conversa e rascunho de plano de privacidade em contexto de saude. O foco e gestao de risco medico-hospitalar: dados sensiveis, prontuario, acesso, fornecedores, retencao, sigilo e resposta a incidente.

## Guardrails
- Toda saida juridica deve comecar com `DRAFT — Requer revisão e assinatura`.
- Esta skill e PRIVACIDADE/LGPD em saude — NÃO cobre responsabilidade/erro medico, defesa de
  processo medico nem negativa de plano de saude. Se o caso for lide medica, avisar que nao ha
  skill para isso e escalar para pesquisa juridica; nao forcar o caso dentro desta estrutura.
- Terminar SEMPRE com "Fora do escopo desta triagem" (o que nao foi analisado).
- Nao afirmar regra CFM/ANS/ANPD, prazo de guarda, base legal ou excecao sem `verificar na fonte primaria`.
- Nao incluir nome de paciente, diagnostico, exame, prontuario ou imagem real em exemplos.
- Se receber prontuario ou dado de saude, tratar como informacao altamente sensivel e redigir antes de logar.
- Nao produzir parecer medico, diagnostico, prognostico ou orientacao clinica.

## Intake
1. Tipo de cliente: clinica, hospital, laboratorio, profissional liberal, healthtech, consultoria.
2. Atividade avaliada: atendimento, prontuario, agendamento, faturamento, pesquisa, telemedicina, compartilhamento com operadora/terceiro.
3. Dados tratados: categorias especificas, sem inserir dados reais.
4. Acesso interno: medico, enfermagem, recepcao, financeiro, TI, terceiros.
5. Sistemas: prontuario, agenda, WhatsApp, nuvem, laboratorio, backup.
6. Retencao/descarte: regra interna e fonte a verificar.
7. Compartilhamentos: operadora, laboratorio, hospital, contador, software, marketing.
8. Incidentes possiveis: vazamento, acesso indevido, envio errado por WhatsApp, perda de backup.

## Checklist
| Tema | Perguntas | Sinal de alerta |
|---|---|---|
| Minimização | coleta somente o necessario? | ficha excessiva sem finalidade |
| Acesso | cada perfil acessa apenas o necessario? | recepcao vendo prontuario integral |
| WhatsApp | ha politica de envio de documentos? | laudos/imagens em conversa aberta |
| Fornecedores | contrato cobre confidencialidade e tratamento? | software sem DPA |
| Retencao | ha prazo e descarte documentados? | "guardar para sempre" sem criterio |
| Titulares | existe fluxo de acesso/correcao? | pedidos tratados caso a caso sem registro |
| Incidente | ha plano de resposta? | ninguem sabe quem acionar |
| Treinamento | equipe entende sigilo? | onboarding sem orientacao |

## Output
```markdown
DRAFT — Requer revisão e assinatura

# Plano de Privacidade em Saude — [CLI-XXX]

## Nota da revisora
- Escopo: [atividade / unidade / sistema]
- Dados de saude: [nao recebidos / redigidos / pendente]
- Normas e prazos a verificar em fonte primaria: [lista]

## Sumario executivo
[2-4 frases de negocio, sem parecer final.]

## Mapa de dados de saude
| Atividade | Dados | Quem acessa | Sistema | Terceiros | Retencao | Lacunas |
|---|---|---|---|---|---|---|

## Riscos medico-hospitalares
| Severidade | Risco | Cenario | Mitigacao | Dono |
|---|---|---|---|---|

## Controles recomendados
- Politica de acesso ao prontuario.
- Politica de WhatsApp e envio de documentos.
- DPA/contrato com fornecedores de software, nuvem e laboratorio.
- Treinamento de equipe.
- Fluxo de atendimento a titular/paciente.
- Plano de resposta a incidente.

## Decisoes para a advogada
- [ ] Confirmar regra setorial aplicavel.
- [ ] Confirmar prazo de retencao aplicavel.
- [ ] Confirmar base de compartilhamento com terceiros.
- [ ] Confirmar se precisa de RIPD separado.
```
