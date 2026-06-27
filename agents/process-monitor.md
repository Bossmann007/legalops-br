---
name: process-monitor
description: Monitora processos nos TJs diariamente e extrai prazos de intimações
schedule: diário às 6h (antes do briefing matinal das 7h)
---

## Missão
Verificar todos os processos cadastrados em busca de movimentações novas desde o último check.
Para cada movimentação que contenha intimação: extrair e registrar prazo automaticamente.

## Execução
```bash
uv run legalops processos --monitorar-todos --desde-ultimo-check
```

Para cada processo com movimentação nova:
1. Classificar: despacho / decisão / intimação / sentença / julgamento
2. Se intimação: extrair data + tipo de ato → registrar prazo via `cpc_prazos`
3. Marcar prazo para alertas D-3 e D-1

## Output
Salvar em `data/monitor/[data].json` com:
- Processos verificados: N
- Com movimentação nova: N
- Prazos extraídos: N
- Erros de conexão: [lista de TJs offline se houver]

## Notificação
Se encontrou movimentações relevantes:
```python
from legalops.notification_multiplex import notify
notify(channel="whatsapp", message="📋 Monitor: N processo(s) com novidade. Use /briefing para ver.")
```

## TJs cobertos
TJPR · TJSP · TJMG · TJSC · TJRJ · TJDFT

## Guardrails
- Se TJ offline: registrar erro, continuar com os outros, notificar no briefing
- Nunca logar conteúdo completo de despacho — apenas tipo e data
- PII: usar `pii_redactor` antes de salvar qualquer texto em log
