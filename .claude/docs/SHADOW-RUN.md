# Shadow-Run — Critério de Pronto da Fase A

O harness de prazos só é considerado "pronto para confiar" depois de rodar **em
paralelo** ao controle manual da advogada por ~2 semanas, com **zero divergência
não explicada**. Concordância entre modelos mede consistência, não correção — só
o controle humano é a verdade.

## Como rodar
1. Toda intimação real que chegar, a advogada processa do jeito de sempre (PJe/Projudi
   + cálculo manual dela) E cola no `/intimacao`.
2. Registre cada caso na tabela abaixo: o que o harness deu vs o que ela deu.
3. Divergência → NÃO ajuste o harness no susto. Investigue a causa raiz, anote em
   "Causa", e só então decida (corrigir engine, corrigir prompt de extração, ou
   aceitar como limitação conhecida).

## Meta de saída
- >= N=15 intimações reais processadas em paralelo.
- Zero divergência de **data final** que não tenha causa explicada e resolvida.
- Todo caso que o oracle mandou para `revisao_manual_obrigatoria` foi, de fato, um
  caso que merecia revisão (sem falso-alarme crônico que treine ela a ignorar).

## Log de divergência

| # | Data | Processo (alias) | Harness (data final) | Manual (data final) | Bateu? | Causa / ação |
|---|------|------------------|----------------------|---------------------|--------|--------------|
| 1 |      |                  |                      |                     |        |              |

## Notas
- Enquanto o shadow-run não fecha, o output continua `DRAFT` e "confira no PJe" — o
  harness é rede de segurança, nunca a fonte. Isso não muda depois; muda só o nível
  de confiança dela no número.
