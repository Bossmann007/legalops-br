# LegalOps BR — PII Gaps & Product Decisions

> Atualizado 2026-05-23 em resposta ao CODE_REVIEW.md secao 4.
> Documenta gaps de redacao deliberados vs bugs reais.

---

## Decisoes de produto (NAO sao bugs)

### 1. Numero CNJ permanece em claro

**Onde:** parser, audit log.

**Justificativa:**
- Numero CNJ (`NNNNNNN-DD.AAAA.J.TR.OOOO`) e **publico por lei** (Res. CNJ 65/2008). Aparece em diarios oficiais, sistemas judiciais publicos (PJe, Projudi, ConsultaProcessual).
- LGPD Art. 5 II nao classifica numero processual como dado pessoal sensivel.
- Removendo CNJ, o sistema perde rastreabilidade — Tia May nao consegue agir sobre alerta sem numero do processo.

**Mitigacao:**
- Egress: ver `SECURITY.md`, seção "Egress / vazamento de PII — postura em camadas".
- Audit `resource` field usa `process:NNNNNNN-...` — facilita query/correlacao sem expor PII.

### 2. Audit log permite metadata com email/OAB/telefone

**Status atual:** `oab_sigilo.py` rejeita CPF/CNPJ/RG bruto no metadata via regex. Email, OAB, telefone passam.

**Decisao:**
- CPF/CNPJ/RG sao indicadores diretos de pessoa fisica/juridica brasileira — bloqueio justificado.
- Email/OAB/telefone podem aparecer em contexto operacional (ex: identificar advogado autor de uma acao). Bloquear inviabilizaria audit util.
- **Mitigacao:** convencionar que metadata so contem placeholders ja redacted pelo `pii_redactor` (`[EMAIL_abc123]`, `[OAB_def456]`).

---

## Gaps reais (TODO future)

### G1. CPF/CNPJ sem mascara nao sao detectados

**Patterns atuais:**
- CPF: `\d{3}\.\d{3}\.\d{3}-\d{2}` (so formato `123.456.789-00`)
- CNPJ: `\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}`

**Vazamento:** `12345678900` (CPF sem mascara) ou `12345678000190` (CNPJ sem mascara) **NAO sao redigidos**.

**Quando importa:**
- Documentos juridicos que mencionam CPF/CNPJ sem formatacao (raro mas possivel em sistemas legados).
- Documentos exportados de planilhas com colunas numericas.

**Fix recomendado (v0.2):**
```python
"CPF_SEM_MASCARA": re.compile(r"\b\d{11}\b"),
"CNPJ_SEM_MASCARA": re.compile(r"\b\d{14}\b"),
```

**Risco do fix:**
- Falso positivo alto: qualquer sequencia de 11/14 digitos vira `[CPF_SEM_MASCARA_xxx]`.
- Ex: numero de cartao de credito (16 digitos) nao colide, mas codigos internos, ids, podem.

**Mitigacao do fix:** validar digito verificador CPF/CNPJ antes de redigir — reduz falso positivo a ~zero.

### G2. Telefone BR sem DDI

**Pattern atual:** `\+?55?\s?\(?\d{2}\)?\s?9?\d{4}-?\d{4}` — exige opcionalmente `+55`.

**Vazamento:** `(41) 9999-8888` redige, mas `99998888` (so 8 digitos) nao.

**Decisao:** numero so 8 digitos e ambiguo demais (pode ser qualquer numero) — manter como esta.

### G3. CEP nao e redigido

**Status:** nenhum pattern para CEP `\d{5}-\d{3}`.

**Decisao:** CEP isolado nao identifica pessoa. Quando aparece em endereco completo, o nome/numero da rua e mais sensivel — esses sim deveriam ser redacted (TODO v0.3, requer NER).

---

## Roadmap de fixes

| Fix | Versao alvo | Esforco | Impacto |
|-----|-------------|---------|---------|
| G1 (CPF/CNPJ sem mascara + digito verif) | v0.2 | medio | alto |
| audit oab_sigilo + email/OAB/phone (opcional) | v0.3 | medio | medio |
| Nomes proprios PT-BR (NER) | v0.4 | alto | alto |
| Endereco completo (NER) | v0.4 | alto | medio |

---

## Auditoria periodica

Rodar mensalmente:

```bash
cd /home/bossmann/Projects/legalops-br
uv run python scripts/measure_redactor.py
uv run python scripts/validate_pipeline.py
```

Targets:
- Recall >= 99% em corpus 500+ docs sinteticos
- Leak rate = 0%
- Pipeline validation = todos casos OK

---

## Referencias

- [[CODE_REVIEW]] (sessao 2026-05-23)
- [[LegalOps — Seguranca e LGPD]]
- [[LegalOps — Roadmap]]
- [[Project 1 — Backend Pipeline]]
