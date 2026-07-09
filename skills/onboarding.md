---
name: onboarding
description: Entrevista guiada para preencher o perfil do escritorio (firm_context + user) na primeira configuracao
triggers: ["/onboarding", "configurar escritorio", "primeira configuracao", "preencher perfil"]
---

Use na PRIMEIRA configuracao com a advogada, ou quando dados do escritorio mudarem. Conduz uma
entrevista curta e grava as respostas reais na pasta LOCAL gitignored `memory.local/`
(`firm_context.local.md`, `user.local.md`, `primer.local.md`) — **nunca** nos templates rastreados
`memory/*.md`. Ver detalhe em "Ao concluir".

## Guardrails
- Uma pergunta por vez, tom direto — a advogada nao tem tempo para formularios longos.
- Nunca inventar dado. Se ela nao souber ou nao quiser responder, deixar `[pendente]` e seguir.
- Nomes de clientes NUNCA em texto puro — registrar so a contagem/estimativa; mapeamento real vai para `data/clientes-aliases.json` (gitignored).
- Ao final, mostrar o que foi preenchido para ela confirmar antes de salvar.

## Roteiro (preencher conforme responde)

### 1. Escritorio
- Nome/razao social · endereco completo · OAB · e-mail profissional
- (WhatsApp e areas ja pre-preenchidos do site — confirmar se corretos)

### 2. Operacao
- Numero estimado de processos ativos
- Numero estimado de clientes ativos
- Sistema atual de controle de prazos (Astrea / planilha / PJe / nada)
- Pessoas na equipe alem dela

### 3. Honorarios (opcional — pode deixar pendente)
- Consulta · acompanhamento mensal · faixa de exito por area
- Formas de pagamento

### 4. Rotina e comunicacao
- Horario que abre o WhatsApp de manha (para o briefing)
- Dia/horario preferido para revisao semanal
- Prefere revisar mensagens antes de enviar a clientes? (default: sim)

### 5. Tribunais e areas
- TJs mais usados (default TJPR)
- Confirmar areas de atuacao do firm_context

## Ao concluir
> Dados REAIS do escritorio NUNCA vao para os arquivos rastreados (`memory/*.md` sao templates).
> Escreva sempre na pasta local gitignored `memory.local/` (nao versionada — ver `.gitignore`).

1. Criar/atualizar `memory.local/firm_context.local.md` e `memory.local/user.local.md`
   com as respostas reais (nome, OAB, endereco, email, WhatsApp, honorarios).
2. Criar/atualizar `memory.local/primer.local.md` (copia do template `memory/Primer.md`
   com a secao "Estado Operacional" preenchida). O SessionStart injeta o `.local` se existir.
3. NUNCA editar `memory/firm_context.md`, `memory/user_tia_may.md` ou `memory/Primer.md`
   com dados reais — sao templates rastreados; o guard `no-real-pii` bloqueia commit se o nome vazar.
4. Mostrar resumo para confirmacao.
5. Sugerir proximo passo: rodar `/briefing` ou cadastrar o primeiro prazo.
