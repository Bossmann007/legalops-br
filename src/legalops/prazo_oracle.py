"""Oracle anti-alucinação para extração de prazos.

Funções puras, determinísticas, zero-token. O LLM extrai; este módulo valida
a extração estruturalmente antes de qualquer cálculo. Nada aqui chama modelo
ou rede — é a rede de segurança que pega a classe de erro que a concordância
entre modelos não pega.
"""

from __future__ import annotations

# Prazos processuais CPC comuns (base, em dias). Fora deste conjunto = suspeito
# de extração errada → revisão manual. NÃO é lista de "prazos válidos por lei";
# é um filtro estrutural de plausibilidade.
LEGAL_PRAZO_SET: frozenset[int] = frozenset({5, 8, 10, 15, 30, 45})


def validate_prazo_dias(prazo_dias: int) -> bool:
    """True se o prazo base pertence ao conjunto legal comum."""
    return prazo_dias in LEGAL_PRAZO_SET
