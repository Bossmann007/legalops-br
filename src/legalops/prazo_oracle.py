"""Oracle anti-alucinação para extração de prazos.

Funções puras, determinísticas, zero-token. O LLM extrai; este módulo valida
a extração estruturalmente antes de qualquer cálculo. Nada aqui chama modelo
ou rede — é a rede de segurança que pega a classe de erro que a concordância
entre modelos não pega.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

# Prazos processuais CPC comuns (base, em dias). Fora deste conjunto = suspeito
# de extração errada → revisão manual. NÃO é lista de "prazos válidos por lei";
# é um filtro estrutural de plausibilidade.
LEGAL_PRAZO_SET: frozenset[int] = frozenset({5, 8, 10, 15, 30, 45})


def validate_prazo_dias(prazo_dias: int) -> bool:
    """True se o prazo base pertence ao conjunto legal comum."""
    return prazo_dias in LEGAL_PRAZO_SET


# Janela de plausibilidade: uma intimação sendo processada não deve ter sido
# publicada no futuro nem há mais de ~1 ano. Fora disso = provável erro de
# extração de data. ponytail: janela fixa, torne configurável se surgir caso real.
MAX_IDADE_PUBLICACAO = timedelta(days=365)


def validate_data_publicacao(data_publicacao: date, *, hoje: date) -> bool:
    """True se a data é <= hoje e não é antiga demais para ser plausível."""
    if data_publicacao > hoje:
        return False
    if hoje - data_publicacao > MAX_IDADE_PUBLICACAO:
        return False
    return True


# Mapa mínimo tribunal → (segmento_justica, codigo_tribunal) do CNJ.
# Só os foros que a advogada realmente toca. Tribunal fora do mapa =
# inconclusivo (None), não bloqueia. ponytail: expanda quando surgir foro novo.
CNJ_TRIBUNAL_MAP: dict[str, tuple[str, str]] = {
    "TJPR": ("8", "16"),
    "TRF4": ("4", "04"),
    "STJ": ("3", "00"),
}

_CNJ_RE = re.compile(r"^\d{7}-\d{2}\.\d{4}\.(\d)\.(\d{2})\.\d{4}$")


def validate_cnj_tribunal(cnj: str, tribunal: str) -> bool | None:
    """Tri-state: True consistente, False conflito, None inconclusivo.

    None quando o CNJ é malformado OU o tribunal não está no mapa mínimo.
    """
    m = _CNJ_RE.match((cnj or "").strip())
    if not m:
        return None
    esperado = CNJ_TRIBUNAL_MAP.get((tribunal or "").upper())
    if esperado is None:
        return None
    return (m.group(1), m.group(2)) == esperado
