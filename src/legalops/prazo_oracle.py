"""Oracle anti-alucinação para extração de prazos.

Funções puras, determinísticas, zero-token. O LLM extrai; este módulo valida
a extração estruturalmente antes de qualquer cálculo. Nada aqui chama modelo
ou rede — é a rede de segurança que pega a classe de erro que a concordância
entre modelos não pega.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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


def is_duplicate(ref: str, ato: str, ledger: list[dict[str, object]]) -> bool:
    """True se (ref, ato) já existe no ledger (ato case-insensitive)."""
    ref_norm = (ref or "").strip()
    ato_norm = (ato or "").strip().lower()
    for item in ledger:
        if (
            str(item.get("ref", "")).strip() == ref_norm
            and str(item.get("ato", "")).strip().lower() == ato_norm
        ):
            return True
    return False


# Campos que determinam o cálculo. Confiança NÃO está aqui de propósito:
# concordância mede consistência estrutural, não auto-avaliação do modelo.
CAMPOS_CHAVE: tuple[str, ...] = (
    "data_publicacao",
    "prazo_dias",
    "parte",
    "tribunal",
    "via_dje",
)


def extractions_agree(a: dict[str, object], b: dict[str, object]) -> bool:
    """True se as duas extrações batem em todos os campos-chave."""
    for campo in CAMPOS_CHAVE:
        if a.get(campo) != b.get(campo):
            return False
    return True


STATUS_OK = "ok"
STATUS_REVISAO = "revisao_manual_obrigatoria"


@dataclass
class Verdict:
    status: str
    reasons: list[str] = field(default_factory=list)
    campos: dict[str, object] = field(default_factory=dict)


def evaluate_extraction(
    a: dict[str, object],
    b: dict[str, object],
    *,
    hoje: date,
    ledger: list[dict[str, object]],
) -> Verdict:
    """Aplica dual-extract + validações estruturais + dedup.

    Retorna veredito ok só se: as duas extrações concordam nos campos-chave,
    todas as validações estruturais passam (CNJ inconclusivo não bloqueia),
    e não é duplicata. Qualquer falha → revisao_manual_obrigatoria.
    """
    reasons: list[str] = []

    if not extractions_agree(a, b):
        divergentes = [c for c in CAMPOS_CHAVE if a.get(c) != b.get(c)]
        reasons.append(f"Divergência entre modelos em: {', '.join(divergentes)}")
        # Divergência é terminal: sem campo consolidável, não seguimos validando.
        return Verdict(status=STATUS_REVISAO, reasons=reasons)

    # A partir daqui as duas concordam; usamos 'a' como fonte consolidada.
    prazo_dias = a.get("prazo_dias")
    if not isinstance(prazo_dias, int) or not validate_prazo_dias(prazo_dias):
        reasons.append(f"prazo_dias fora do conjunto legal: {prazo_dias!r}")

    data_pub_raw = a.get("data_publicacao")
    try:
        data_pub = date.fromisoformat(str(data_pub_raw))
        if not validate_data_publicacao(data_pub, hoje=hoje):
            reasons.append(f"data_publicacao implausível: {data_pub_raw!r}")
    except (TypeError, ValueError):
        reasons.append(f"data_publicacao inválida: {data_pub_raw!r}")

    cnj_ok = validate_cnj_tribunal(str(a.get("cnj", "")), str(a.get("tribunal", "")))
    if cnj_ok is False:
        reasons.append(f"CNJ inconsistente com tribunal {a.get('tribunal')!r}: {a.get('cnj')!r}")

    if is_duplicate(str(a.get("ref", "")), str(a.get("ato", "")), ledger):
        reasons.append(f"Duplicata no ledger: ref={a.get('ref')!r} ato={a.get('ato')!r}")

    if reasons:
        return Verdict(status=STATUS_REVISAO, reasons=reasons)
    return Verdict(status=STATUS_OK, reasons=[], campos=dict(a))
