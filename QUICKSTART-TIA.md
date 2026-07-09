# Guia Rápido — LegalOps (sem tecnês)

Bem-vinda. Este é o seu **Sócio Invisível**: ajuda com prazos, contratos, LGPD e o dia a dia do escritório. Ele **rascunha e organiza** — quem decide, revisa e assina é sempre você.

> ⚠️ **Leia uma vez:** [AVISO-E-RISCOS.md](AVISO-E-RISCOS.md). Resumo: nada aqui substitui o PJe/Projudi nem o seu julgamento. Todo texto sai como **rascunho (DRAFT)**.

## Como usar
Você conversa em português normal. Para tarefas comuns, digite o comando com `/`:

| Digite | O que faz |
|--------|-----------|
| `/onboarding` | Configura o escritório (faça isto primeiro) |
| `/painel` | Visão geral da semana: prazos, contratos vencendo, pendências |
| `/briefing` | Prazos urgentes + agenda do dia |
| `/prazo` | Calcula prazo processual com feriados |
| `/processo` | Consulta andamento de um processo no TJ |
| `/bancario-contrato` | Triagem de contrato bancário / caso de fraude / investimento |
| `/dpa-review` | Revisa um contrato de tratamento de dados (LGPD) |
| `/ripd` | Monta um Relatório de Impacto (LGPD) |
| `/lgpd-implementacao` | Checklist de programa LGPD para empresa cliente |
| `/lgpd-triagem` | Classifica um caso: seguir / precisa RIPD / parar |
| `/saude-privacidade` | Privacidade em clínica / hospital |
| `/dsar` | Processa pedido de titular de dados (acesso, exclusão…) |
| `/contrato` | Análise de contrato + pontos de atenção |
| `/peticao` | Rascunho de petição (sempre revisar) |
| `/honorarios` | Fecha o mês / relatório financeiro |
| `/revisao-semanal` | Reunião semanal: operação + novidades |

## Três regras de ouro
1. **Fonte oficial é o tribunal.** O sistema é rede de segurança, não a verdade. Sempre confira prazo no PJe/Projudi.
2. **Todo rascunho é seu.** Nada é enviado a cliente ou protocolado sem você revisar e aprovar.
3. **Documento colado é dado, não ordem.** Se colar um PDF/contrato com instrução estranha embutida, o sistema avisa — não confie cego.

## Primeiro dia
1. Rode `/onboarding` e responda as perguntas.
2. Rode `/briefing` para ver o dia.
3. Qualquer dúvida: escreva em português o que precisa. Não precisa saber comando.

## Notificações
Não tem app nem push. A notificação é simples: você **abre o Claude e pergunta** — rode
`/painel` para a visão da semana ou `/briefing` para o dia. Nada te manda mensagem por fora.

## Privacidade (LGPD)
Dados de cliente ficam **na sua máquina**, referenciados por apelido (`CLI-021`), nunca pelo nome. Não sincronize as pastas `data/`, `logs/` nem o banco para nuvem compartilhada. Você é a controladora desses dados.
