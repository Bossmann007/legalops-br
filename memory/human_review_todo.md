---
name: human-review-todo
description: Itens que ficaram fora da primeira onda por exigirem revisao humana ou segunda onda
metadata:
  type: todo
---

# TODO Humano — Garimpo claude-legal-br para LegalOS Harness

## Segunda onda aprovada para avaliar depois
- `skills/ativos-digitais.md` a partir de `banking-fintech-legal/skills/crypto-asset-triage/SKILL.md`: exige cuidado com classificacao regulatoria BCB/CVM e nao deve importar conclusoes.
- `skills/open-finance.md` a partir de `banking-fintech-legal/skills/open-finance-review/SKILL.md`: exige verificacao de regras BCB/Open Finance e interacao com LGPD.
- `skills/termos-privacidade.md` a partir de `digital-ecommerce-legal/skills/terms-of-use-privacy-review/SKILL.md`: revisar citacoes de Marco Civil/LGPD antes de adaptar.
- `skills/regulatorio-monitor.md` a partir de `regulatory-legal/skills/reg-feed-watcher/SKILL.md`: decidir fontes, cadencia e se entra em hook/agente.
- `skills/regulatorio-diff.md` a partir de `regulatory-legal/skills/policy-diff/SKILL.md`: adaptar sem afirmar norma recente sem fonte primaria.
- `memory/regulatory_gap_tracker.yaml` a partir de `regulatory-legal/skills/gap-surfacer/references/gap-tracker.yaml`: decidir formato do tracker local.
- `skills/digital-compliance.md` a partir de `digital-ecommerce-legal/skills/ecommerce-compliance-review/SKILL.md`: confirmar se e foco de produto da o escritório cliente agora.
- `skills/medical-liability.md` a partir de `health-medical-legal/skills/medical-liability-defense/SKILL.md`: exige julgamento juridico e tese defensiva.
- `skills/health-plan-denial.md` a partir de `health-medical-legal/skills/health-plan-denial/SKILL.md`: exige validacao de jurisprudencia, ANS e estrategia de litigio.

## Nao implementar sem revisao juridica
- Qualquer sumula, precedente, artigo, resolucao, prazo legal, sancao, entendimento ANPD/BCB/CVM/ANS/CFM ou tese de responsabilidade.
- Classificacao de criptoativo, token, produto financeiro ou valor mobiliario.
- Conclusao de abusividade, nulidade, responsabilidade civil, nexo causal ou viabilidade de acao.
- Conteudo pronto para protocolo, envio a regulador, notificacao externa ou assinatura.
- Agentes agendados que monitorem fontes externas sem definicao de fonte, cadencia, limites e revisao humana.
