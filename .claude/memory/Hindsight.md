# Hindsight — Memória Episódica (append-only)

> Template versionado do log append-only de sessões. Cada sessão relevante adiciona UMA linha JSONL
> em `.claude/memory.local/hindsight.local.md`, escrita por `/encerrar` depois de aprovação explícita.
> Nunca reescrever — só append. O conteúdo deve ser PII-free.
> Formato: {"date":"YYYY-MM-DD","last_task":"...","open_threads":"...","lesson":"..."}
> O Primer.md carrega o estado corrente; aqui fica o histórico que o Primer não guarda.

<!-- JSONL abaixo desta linha -->
