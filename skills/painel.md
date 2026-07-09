---
name: painel
description: Renderiza o painel operacional do escritorio como um Artifact HTML — prazos, contratos vencendo, pendencias. Substitui o dashboard web.
triggers: ["/painel", "painel", "como esta a semana", "dashboard", "visao geral"]
---

Monta uma visao geral do escritorio como **um Artifact HTML** dentro do Claude. Nao sobe
servidor, nao abre porta, nao expoe nada na rede — o dado fica na maquina, o painel e efemero
na sessao. Substitui o antigo dashboard web (deprecated no piloto).

## Guardrails
- E rede de segurança, nao fonte oficial: todo prazo mostrado leva o aviso "conferir no PJe/Projudi".
- Cliente sempre por **alias** (`CLI-XXX`) — nunca nome real no painel.
- Nenhum dado sai da maquina: o Artifact e HTML self-contained, sem fetch externo.

## Coletar estado (local)
Rode e junte o que existir; se um comando nao tiver dado, mostre a secao vazia, nao invente:
```bash
# Contratos vencendo / renovacao
uv run legalops renovacao --hoje AAAA-MM-DD
# Estado corrente do escritorio (prazos abertos, threads, DSARs)
cat memory.local/primer.local.md 2>/dev/null || cat memory/Primer.md
```
Para prazos individuais que a advogada acompanha, calcule cada um com
`uv run legalops prazo --data-publicacao ... --prazo-dias N --parte ... --hoje AAAA-MM-DD`.

## Renderizar (Artifact HTML self-contained)
Produza UM Artifact HTML com estes cards, em portugues, responsivo, tema claro/escuro:

1. **Prazos (D-7)** — semaforo: 🔴 ≤1 dia · 🟠 ≤3 · 🟢 >3. Colunas: processo (mascarado),
   ato, data-limite, dias restantes. Rodape do card: "Conferir no PJe/Projudi — fonte oficial."
2. **Contratos vencendo** — alias, dias ate evento, urgencia (dos alertas de `renovacao`).
3. **Pendencias / threads** — do Primer (o que ficou aberto).
4. **DSARs abertos** — se houver, com SLA interno e "confirmar prazo em fonte primaria".

Regras do Artifact: HTML self-contained (CSS/JS inline, sem CDN, sem fetch), sem nome real
de cliente, sem PII. Cabecalho: "Painel — [data]". Se tudo vazio, mostre "Sem pendencias
registradas" e sugira `/onboarding` ou cadastrar o primeiro prazo.
