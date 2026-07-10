# Instintos — Preferências Aprovadas

> Template versionado. Os instintos reais ficam apenas em
> `.claude/memory.local/instincts.local.md` (gitignored).
>
> Antes de gravar, o assistente resume o texto, mostra a proposta e espera a aprovação explícita
> “sim”. Cada linha deve ser PII-free: pode registrar estilo, fluxo, defaults ou aliases, nunca
> nome, CPF, OAB, e-mail, telefone, processo ou outro dado real.

Formato de cada instinto:

```text
- [id-curto] QUANDO <gatilho> ENTÃO <comportamento> (aprovado AAAA-MM-DD)
```

Exemplos válidos:

```text
- [tjpr-padrao] QUANDO consultar tribunal sem indicação ENTÃO usar TJPR como padrão (aprovado 2026-07-10)
- [tom-formal] QUANDO redigir petição ENTÃO usar tom formal (aprovado 2026-07-10)
- [honorarios-sexta] QUANDO chegar sexta-feira ENTÃO sugerir revisão de honorários (aprovado 2026-07-10)
- [prazo-duplo] QUANDO mostrar prazo ENTÃO informar dias úteis e corridos (aprovado 2026-07-10)
```

Exemplos proibidos: qualquer preferência que contenha nome real, CPF, OAB, número de processo ou
outro dado pessoal.
