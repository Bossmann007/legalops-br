# CLI Bridges v0.3 — Contract for Dashboard Wiring

Four internal M&A / societário modules exposed as `legalops` CLI subcommands.
All emit **JSON to stdout**, indented 2, UTF-8 (`ensure_ascii=False`). All take
args via **flags** (no stdin). Exit codes documented per command.

Synthetic data only — the `no-real-pii` pre-commit hook blocks real names/CPFs.
These adapters are thin: they build the domain objects from flat CLI args and
call the existing functions without redaction (inputs are aliases, not raw PII).

Run prefix: `LEGALOPS_PII_SALT=<salt> uv run legalops <subcommand> ...`
(salt not strictly required by these 4 commands — none invoke the PII redactor —
but the global env contract still applies.)

---

## 1. `societario`

Validates coherence of equity participation (CC/2002) via `validar_participacoes`.

### Args
| Flag | Required | Type | Notes |
|------|----------|------|-------|
| `--socios` | yes | JSON string | list of objects (shape below) |
| `--tipo` | no | enum | `ltda` (default), `sa_fechada`, `sa_aberta`, `eireli`, `mei`, `slu`, `desconhecido` |
| `--cnpj` | no | string | digits or formatted; validated by check digit |
| `--capital-social` | no | float | optional |

`--socios` element shape:
```json
{ "nome_alias": "SOCIO-A", "percentual": 60, "tipo": "quotista" }
```
- `nome_alias` (string, optional — defaults to `socio-<idx>`). **Alias only, never real PII.**
- `percentual` (number, required) — participation 0..100.
- `tipo` (string, optional, default `quotista`) — one of `administrador`, `quotista`, `acionista`.

### Exit codes
- `0` — coherent (no problems)
- `1` — incoherent (problems found)
- `2` — bad input (invalid JSON / not a list / item not object / bad `tipo` / missing/non-numeric `percentual`)

### Sample
```
legalops societario --tipo ltda --socios '[{"nome_alias":"SOCIO-A","percentual":60,"tipo":"quotista"},{"nome_alias":"SOCIO-B","percentual":40,"tipo":"administrador"}]'
```
```json
{
  "tipo": "ltda",
  "cnpj": null,
  "n_socios": 2,
  "soma_participacoes": 100,
  "coerente": true,
  "problemas": []
}
```
Error sample (exit 2):
```json
{ "error": "socios JSON invalido: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)" }
```

---

## 2. `vendor-review`

Emits the **standard** AI-vendor LGPD review checklist via `checklist_vendor_padrao()`.

> The underlying API takes **no vendor/finalidade input** — it returns a fixed
> standard checklist for downstream fill-in. The adapter surfaces this in
> `--help` and in the `nota` field. There is no per-vendor parameterization.

### Args
| Flag | Required | Type | Notes |
|------|----------|------|-------|
| `--format` | no | enum | `json` (default) or `text` |

### Exit codes
- `0` — always (read-only emit)

### Sample
```
legalops vendor-review --format json
```
```json
{
  "checklist": "vendor_ai_review_padrao",
  "nota": "API nao recebe vendor/finalidade; emite checklist padrao.",
  "score": 0.0,
  "aprovado": false,
  "itens": [
    {
      "chave": "transferencia_internacional",
      "pergunta": "Ha transferencia internacional de dados e ela atende ao Art. 33?",
      "artigo": "Art. 33",
      "status": "pendente",
      "obrigatorio": true
    }
  ]
}
```
(10 items total; all `status: "pendente"` on emit. `--format text` prints a
human list instead of JSON.)

---

## 3. `disclosure`

Cross-checks representations vs disclosure schedule — `find_gaps` + `inconsistencias`.

### Args
| Flag | Required | Type | Notes |
|------|----------|------|-------|
| `--representacoes` | yes | JSON string | list of objects (shape below) |
| `--schedule` | no | JSON string | list of objects; defaults to empty |

`--representacoes` element shape:
```json
{ "id": "R-4.1", "texto": "...", "requer_schedule": true }
```
- `id` (string, **required**).
- `texto` (string, optional, default `""`).
- `requer_schedule` (bool, optional, default `true`).

`--schedule` element shape:
```json
{ "rep_id": "R-4.1", "conteudo": "..." }
```
- `rep_id` (string, **required**).
- `conteudo` (string, optional, default `""`).

### Exit codes
- `0` — no gaps and no inconsistencias
- `1` — at least one gap or inconsistencia
- `2` — bad input (invalid JSON / not a list / missing `id` / missing `rep_id`)

### Sample
```
legalops disclosure --representacoes '[{"id":"R-1","texto":"rep um","requer_schedule":true}]' --schedule '[]'
```
```json
{
  "n_representacoes": 1,
  "n_schedule_items": 0,
  "gaps": [ { "id": "R-1", "texto": "rep um" } ],
  "inconsistencias": []
}
```
(`inconsistencias` elements are `{ "rep_id": "...", "conteudo": "..." }`.)

---

## 4. `due-diligence`

Emits the standard BR due-diligence checklist via `checklist_padrao()`, with an
optional area filter applied in the adapter.

> The underlying API takes no input. `--area` filters which items are emitted.

### Args
| Flag | Required | Type | Notes |
|------|----------|------|-------|
| `--area` | no | enum | `trabalhista`, `fiscal`, `ambiental`, `contratual`, `societario`; omit for all |

### Exit codes
- `0` — always (read-only emit)

### Sample
```
legalops due-diligence --area fiscal
```
```json
{
  "checklist": "due_diligence_padrao",
  "area_filtro": "fiscal",
  "n_itens": 3,
  "score": 0.0,
  "itens": [
    {
      "area": "fiscal",
      "descricao": "Certidao de tributos federais",
      "obrigatorio": true,
      "referencia": "CND Receita Federal",
      "status": "pendente"
    }
  ]
}
```
(Full checklist without `--area` has 13 items across 5 areas. `area_filtro` is
`null` when no filter is given.)

---

## Summary

| Subcommand | Required arg(s) | Exit 0/1/2 |
|------------|-----------------|------------|
| `societario` | `--socios` (JSON list) | 0 coherent / 1 problems / 2 bad input |
| `vendor-review` | — | 0 only |
| `disclosure` | `--representacoes` (JSON list) | 0 clean / 1 findings / 2 bad input |
| `due-diligence` | — (`--area` optional) | 0 only |
