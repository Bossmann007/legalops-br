---
name: varrer
description: Checa a caixa de email (Outlook/M365) por intimações novas, tria e manda pro cálculo de prazo. Rede de segurança, não fonte oficial.
triggers: ["/varrer", "checar caixa", "tem intimacao nova", "varrer email"]
---

## Proveniência obrigatória
Na saída, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Campo extraído
de email ou intimação recebe `[documento do usuário]`; prazo calculado pelo pipeline local recebe
`[motor determinístico]`; e regra não conferida recebe
`[conhecimento do modelo — conferir]`. Uma etiqueta geral não basta.

Checa a caixa dela por intimações novas: $ARGUMENTS

Fonte oficial é o PJe/Projudi — isto é rede de segurança. Você NUNCA calcula prazo;
o cálculo é sempre o pipeline determinístico. Siga a ordem:

## 0. Preflight — o conector está acessível?
Confirme que a ferramenta MCP de email (Outlook/M365) está conectada e responde.
Se NÃO estiver (sem conector, auth expirada, erro):
```bash
uv run legalops scan-state --set --resultado falha --quando <ISO-agora>
```
E PARE com o aviso: "NÃO consegui olhar sua caixa (a conexão com o Outlook pode ter
caído). NÃO assuma que não há prazo. Reconecte o Outlook e rode `/varrer` de novo,
ou cole a intimação no `/intimacao`."
➡️ Próximo: `/intimacao`

## 1. Buscar (MCP, só leitura)
Busque emails dos últimos 7 dias. NUNCA mova, apague nem responda email — só leia.
Monte uma lista `[{sender, subject, data (AAAA-MM-DD), body}]` e salve em
`data/tmp/caixa.json`.

## 2. Triagem determinística
```bash
uv run legalops triagem --input data/tmp/caixa.json --janela 7 --hoje AAAA-MM-DD
```
Retorna `candidatos` (só os de tribunal, com `tribunal` e `data_suspeita`).
- Se `candidatos` vazio → varredura sem intimação nova:
```bash
uv run legalops scan-state --set --resultado vazio --quando <ISO-agora> --n-encontrados 0
```
Diga: "Última varredura: agora — nenhuma intimação nova na caixa."
➡️ Próximo: `/painel`

## 3. Confirmação da advogada
Mostre a lista mascarada (sem PII real): `[tribunal | assunto | data]`, marcando
`data_suspeita` quando houver. Peça: "Quais destes são intimação de verdade pra
processar? (número(s), ou 'todos')". Só siga com os confirmados.

## 4. Redação + pipeline (só confirmados)
Redija PII de cada confirmado ANTES de qualquer modelo ver. Rode o Workflow
`intimacoes-batch` (Fase A) com os textos redigidos. Ele faz dual-extract + oracle +
cálculo determinístico; prazos válidos entram no ledger, o resto vira revisão manual.

## 5. Registrar estado
```bash
uv run legalops scan-state --set --resultado ok --quando <ISO-agora> \
  --n-encontrados <N> --n-processados <N_ok> --n-revisao <N_revisao>
```

## 6. Surface
```
DRAFT — Requer revisão e assinatura

📥 Varredura concluída — <N_ok> prazo(s) calculado(s), <N_revisao> para revisão manual.

Última varredura: agora.
```
- Se houve revisão manual: liste os motivos e diga "Confira no PJe/Projudi e, se for
  o caso, cole no `/intimacao`."
➡️ Próximo: `/painel`

## Regras
- Só LÊ email (nunca move/apaga/responde) — reversibilidade.
- Cliente por alias, nunca nome real na lista de triagem.
- Você NUNCA calcula prazo — se o pipeline não rodar, RECUSE e mande conferir no PJe.
- MCP indisponível = fail-closed (passo 0). Nunca renderize vazio como "nada novo".
