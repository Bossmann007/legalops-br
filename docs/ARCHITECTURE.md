# Architecture — LegalOps BR

## Visão geral

Pipeline local-first em 4 camadas, com gates LGPD entre cada uma.

```
┌──────────────────────────────────────────────────────────┐
│  email_text (raw, com PII)                                │
└─────────────────────────┬─────────────────────────────────┘
                          ▼
              ┌────────────────────────┐
              │ pii_redactor (LGPD)   │  ← regex BR + SHA-256 salted placeholders
              │ - CPF/CNPJ/OAB/etc    │  ← validators: módulo 11 pra numéricos
              └───────────┬────────────┘
                          ▼
              ┌────────────────────────┐
              │ tribunal_detector      │  ← sender domain + header fingerprint
              │ → tjsp/tjpr/tjsc/tjrj │
              └───────────┬────────────┘
                          ▼
              ┌────────────────────────┐
              │ {tjpr,tjsp,…}_parser   │  ← regex CNJ, vara, tipo_ato, prazo
              │ → Intimacao[]          │
              └───────────┬────────────┘
                          ▼
              ┌────────────────────────┐
              │ cpc_prazos             │  ← CPC/2015 deterministico
              │ - dies a quo / ad quem │  ← feriados + recesso + dobro Fazenda
              │ - alerta URGENTE/etc   │
              └───────────┬────────────┘
                          ▼
              ┌────────────────────────┐
              │ oab_sigilo (audit)     │  ← SHA-256 chain SQLite
              └───────────┬────────────┘
                          ▼
              ┌────────────────────────┐
              │ whatsapp_notifier      │  ← bridge.js :3000, só URGENTE, sem PII
              └────────────────────────┘
```

## Gates LGPD (defesa em profundidade)

| Camada | Gate | Mecanismo |
|--------|------|-----------|
| Network | GalileuCLI (Go MITM) | Proxy :9000 redige payloads cross-app |
| Aplicacional | pii_redactor | Regex BR + validators |
| Audit | oab_sigilo metadata | Regex pre-insert rejeita PII em logs |
| Egress (LLM) | claude.ai manual | Cópia-cola humana (zero auto-call) |
| Notification | whatsapp_notifier | Formato fixo: só CNJ + dies ad quem |

## Multiplex de parsers

`orchestrator.process_email()` decide qual parser usar:

```python
tribunal = detect_tribunal(email_text, sender=sender)
parser = _PARSERS.get(tribunal, parse_tjpr)  # fallback TJPR
```

Todos parsers retornam `Intimacao` dataclass (shape único). TJSC/TJRJ atualmente reusam engine TJSP (e-Proc/PJe ~ e-SAJ).

## Determinismo do cpc_prazos

- Feriados nacionais hardcoded (Lei 14.759/2023 inclusa)
- Feriados móveis: Páscoa + ofsets (Carnaval, Sexta Santa, Corpus Christi)
- Recesso forense: 20/12–20/01 (TJPR/STJ/STF/TRF4/TST mesma faixa)
- Dobro Fazenda/MP/Defensoria: Art. 183/180/186 CPC
- Via DJE: Art. 231 #1 (publicação + 1 dia útil)

Sem chamadas externas. Mesma entrada → mesma saída. Validado contra 38 golden tests.

## CI/CD

- GitHub Actions workflow `.github/workflows/ci.yml`:
  uv install → corpus gen → ruff → mypy → pytest → validate_pipeline → measure_redactor
- Pre-commit hooks: ruff (fix), ruff-format, mypy, pytest (pre-push), no-real-pii (bash), detect-private-key

## Não-objetivos

- Auto-call para API claude.ai (nunca — copy-paste manual)
- OCR de PDFs scaneados (fora de escopo v0.x)
- Integração direta com TJs (sem APIs oficiais — usa email forwarding)
- Persistência de PII original (apenas hash SHA-256 salted)
