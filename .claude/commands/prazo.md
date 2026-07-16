---
name: prazo
description: Calcula prazo processual CPC (dias úteis, recesso e feriados nacionais) — calibrado para TJPR
triggers: ["/prazo", "calcular prazo", "quando vence", "prazo para"]
---

## Proveniência obrigatória
Na saída, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Data, prazo,
recesso e feriado calculados pelo CLI recebem `[motor determinístico]`; dado extraído do texto
fornecido recebe `[documento do usuário]`; e regra não conferida recebe
`[conhecimento do modelo — conferir]`. Uma etiqueta geral não basta.

Calcule o prazo para: $ARGUMENTS

## Como funciona (e o que NÃO cobre)
O cálculo é feito pelo subcomando determinístico `legalops prazo`, que aplica: contagem em
dias úteis, dies a quo, prazo em dobro e recesso forense. **Não recalcule à mão citando
artigos de lei** — se o comando não cobrir o caso, diga que precisa de conferência na fonte
primária; nunca invente a regra (RULES #3).

**Limites REAIS deste cálculo — avise a advogada:**
- Recesso/feriado calibrado para **TJPR** (foro dela). Para outro tribunal, o cálculo pode
  estar errado — trate como estimativa e confira no tribunal.
- **Não cobre** feriado municipal (ex.: 8/set em Curitiba), suspensão de expediente por
  portaria/decreto, nem prazo material (prescrição/decadência, que corre em dias corridos).
- É rede de segurança, **não** a fonte oficial. A fonte é o PJe/Projudi.

## Fluxo
1. Se faltar dado (data de publicação, nº de dias do prazo, tribunal, tipo de parte): pergunte.
2. Se for prazo **material** (prescrição, decadência, prazo para ajuizar): NÃO use este cálculo
   processual — avise que corre em dias corridos e exige conferência jurídica.
3. Executar:
```bash
uv run legalops prazo \
  --data-publicacao AAAA-MM-DD \
  --prazo-dias N \
  --parte [particular|fazenda|mp|defensoria] \
  --tribunal TJPR \
  --hoje AAAA-MM-DD
# --via-dje  → intimação pelo Diário eletrônico
```
Retorna JSON com `data_final`, dias corridos e flags de dobro/recesso aplicados.
Se a advogada pedir para acompanhar no painel, rode de novo com registro local explícito:
```bash
uv run legalops prazo \
  --data-publicacao AAAA-MM-DD \
  --prazo-dias N \
  --parte [particular|fazenda|mp|defensoria] \
  --tribunal TJPR \
  --hoje AAAA-MM-DD \
  --salvar \
  --ref PROC-XXX \
  --ato "[desc curta]"
```
Esse `--salvar` apenas anexa em `data/prazos.json` (gitignored) para o `/painel`.
Não cria alerta automático e não é fonte oficial.

## Formato de Resposta
```
DRAFT — Requer revisão e assinatura

📅 Cálculo de Prazo (rede de segurança — não é a fonte oficial)

Data da publicação: DD/MM/AAAA [documento do usuário]
Prazo base: N dias úteis [documento do usuário] · Em dobro? [Sim/Não] [motor determinístico]
Tribunal: TJPR (recesso/feriado calibrado só p/ TJPR)

⚖️ Data final estimada: **DD/MM/AAAA** [motor determinístico]

⚠️ CONFIRA no PJe/Projudi antes de confiar. Este cálculo não cobre feriado municipal,
   suspensão de expediente, nem prazo material. O `--salvar` é só registro local —
   o sistema NÃO envia alerta automático.
```
