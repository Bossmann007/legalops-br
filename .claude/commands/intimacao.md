---
name: intimacao
description: Processa uma intimação/publicação colada — extrai, valida em dois modelos, calcula prazo determinístico e registra. Rede de segurança, não fonte oficial.
triggers: ["/intimacao", "colei uma intimacao", "processar intimacao", "nova publicacao"]
---

## Proveniência obrigatória
Na saída, aplique a Regra 3 de `.claude/RULES.md` **em cada afirmação jurídica**. Campo extraído
da intimação recebe `[documento do usuário]`; prazo, recesso ou feriado calculado pelo CLI
recebe `[motor determinístico]`; e regra não conferida recebe
`[conhecimento do modelo — conferir]`. Uma etiqueta geral não basta.

Processa UMA intimação que a advogada colou: $ARGUMENTS

Fonte oficial é o PJe/Projudi — isto é rede de segurança. O prazo é calculado SÓ pelo engine determinístico; você NUNCA calcula prazo de cabeça. Siga a ordem exata:

## 0. Preflight fail-closed
```bash
uv run legalops calc-disponivel
```
Se o exit code não for 0 (ou `disponivel: false`): PARE. Diga em linguagem simples: "Não consegui rodar o cálculo de prazo agora (o motor não respondeu). NÃO vou estimar de cabeça — isso seria arriscado. Confira o prazo direto no PJe/Projudi e tente de novo." Não continue.

## 1. Redação de PII (antes de qualquer modelo ver o texto)
Redija o texto colado ANTES de despachar os extratores: substitua nomes de pessoas, CPF, OAB e telefones por placeholders. Nenhum dado real de cliente vai para o passo 2.

## 2. Dual-extract (dois modelos diferentes, independentes)
Despache os DOIS subagents com o MESMO texto redacted, em paralelo:
- `prazo-extractor-haiku` → salve a saída JSON em `data/tmp/extr-a.json`
- `prazo-extractor-sonnet` → salve a saída JSON em `data/tmp/extr-b.json`

Cada um retorna só JSON. Não edite as saídas — elas alimentam o oracle cru.

## 3. Oracle (validação determinística)
```bash
uv run legalops validar-extracao --file-a data/tmp/extr-a.json --file-b data/tmp/extr-b.json --hoje AAAA-MM-DD
```
Ramifique pelo EXIT CODE, não pelo texto:
- **exit 0** (`status: ok`) → siga para o passo 4.
- **exit 3** (`revisao_manual_obrigatoria`) → PULE o cálculo. Mostre as `reasons` em linguagem simples e diga: "Os dois modelos não bateram / a validação falhou — não vou calcular sozinho. Confira no PJe/Projudi." NÃO invente o prazo. NÃO escolha uma das extrações "no olho".

## 4. Cálculo determinístico (só se o oracle deu ok)
Use os campos consolidados (`campos` do veredito):
```bash
uv run legalops prazo \
  --data-publicacao <campos.data_publicacao> \
  --prazo-dias <campos.prazo_dias> \
  --parte <campos.parte> \
  --tribunal <campos.tribunal> \
  --hoje AAAA-MM-DD \
  [--via-dje se campos.via_dje] \
  --salvar --ref <campos.cnj ou PROC-XXX> --ato <campos.tipo_ato>
```
Se este comando falhar (exit != 0): fail-closed de novo — NÃO estime. Avise e mande conferir no PJe.

## 5. Surface (DRAFT)
```
DRAFT — Requer revisão e assinatura

📥 Intimação processada (rede de segurança — não é a fonte oficial)

Processo: <CNJ mascarado>  ·  Tribunal: <sigla> [documento do usuário]
Ato: <tipo_ato> [documento do usuário]  ·  Prazo base: <prazo_dias> dias úteis
[documento do usuário]  ·  Em dobro? <sim/não> [motor determinístico]

⚖️ Data final estimada: **DD/MM/AAAA** [motor determinístico]
Registrado no ledger local (aparece no /painel).

⚠️ CONFIRA no PJe/Projudi antes de confiar. Não cobre feriado municipal,
   suspensão de expediente, nem prazo material. Fonte oficial = PJe/Projudi.
```

## Regras
- Cliente sempre por alias (`CLI-XXX` / `PROC-XXX`), nunca nome real.
- Você NUNCA calcula prazo — se o engine não rodou, RECUSE e diga por quê.
- Divergência entre modelos ou validação falha = revisão manual, sem exceção.
