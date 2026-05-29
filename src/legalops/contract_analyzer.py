"""Contract AI — analise de contratos BR (fase v1.2 do roadmap).

Detecta clausulas abusivas (CDC Art. 51 + jurisprudencia BACEN/CDC), analisa
contratos de financiamento (spread, indexador, capitalizacao) e produz um
relatorio de risco pontuado com recomendacoes.

Roda DEPOIS do pii-redactor-br — assume texto sem PII bruto e nunca loga o
conteudo do contrato.

Uso:
    >>> from legalops.contract_analyzer import analisar_contrato
    >>> rel = analisar_contrato("... clausula de eleicao de foro ... juros capitalizados ...")
    >>> rel.score > 0
    True
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "AnaliseFinanciamento",
    "ClausulaAbusiva",
    "RelatorioRisco",
    "Severidade",
    "TipoClausulaAbusiva",
    "analisar_contrato",
    "analisar_financiamento",
    "scan_clausulas_abusivas",
    "scan_nda",
]

TipoClausulaAbusiva = Literal[
    "renuncia_direito",
    "multa_excessiva",
    "juros_capitalizados",
    "reajuste_unilateral",
    "rescisao_unilateral",
    "limitacao_reembolso",
    "inversao_onus",
    "foro_eleicao_adesao",
    "eleicao_arbitragem_compulsoria",
    "desconhecido",
]

Severidade = Literal["baixa", "media", "alta"]

_TRECHO_JANELA = 160


@dataclass(frozen=True)
class ClausulaAbusiva:
    """Uma clausula potencialmente abusiva identificada no contrato."""

    tipo: TipoClausulaAbusiva
    severidade: Severidade
    fundamento: str
    trecho: str


@dataclass(frozen=True)
class AnaliseFinanciamento:
    """Resultado da analise de um contrato de financiamento/credito."""

    spread_pct: float | None = None
    taxa_juros_mensal_pct: float | None = None
    indexador: str | None = None
    capitalizacao_mensal: bool = False
    iof_presente: bool = False
    alertas: tuple[str, ...] = ()


@dataclass
class RelatorioRisco:
    """Relatorio consolidado de risco de um contrato."""

    score: int = 0
    nivel: Literal["baixo", "medio", "alto"] = "baixo"
    clausulas: list[ClausulaAbusiva] = field(default_factory=list)
    financiamento: AnaliseFinanciamento | None = None
    recomendacoes: list[str] = field(default_factory=list)


# --- Clausulas abusivas (CDC Art. 51) -------------------------------------

_SEVERIDADE_PESO: dict[Severidade, int] = {"baixa": 1, "media": 3, "alta": 5}

_CLAUSULA_PATTERNS: tuple[tuple[TipoClausulaAbusiva, Severidade, str, re.Pattern[str]], ...] = (
    (
        "renuncia_direito",
        "alta",
        "CDC Art. 51, I — renuncia previa de direito do consumidor e nula.",
        re.compile(
            r"\b(renuncia(?:r)?|abdica(?:r)?|abre\s+m[ãa]o)\b[^.]{0,80}\bdireito",
            re.IGNORECASE,
        ),
    ),
    (
        "inversao_onus",
        "media",
        "CDC Art. 51, VI — clausula que inverte onus em prejuizo do consumidor.",
        re.compile(r"\b[ôo]nus\s+da\s+prova\b", re.IGNORECASE),
    ),
    (
        "rescisao_unilateral",
        "alta",
        "CDC Art. 51, XI — rescisao unilateral pelo fornecedor sem igual direito.",
        re.compile(
            r"\brescis[ãa]o\b[^.]{0,60}\b(unilateral|a\s+crit[ée]rio|exclusivo\s+crit[ée]rio)",
            re.IGNORECASE,
        ),
    ),
    (
        "reajuste_unilateral",
        "media",
        "CDC Art. 51, X/XIII — variacao de preco/reajuste de forma unilateral.",
        re.compile(
            r"\b(reajust|atualiz|altera)[a-z]*\b[^.]{0,60}\b(unilateral|a\s+crit[ée]rio)",
            re.IGNORECASE,
        ),
    ),
    (
        "multa_excessiva",
        "media",
        "CDC Art. 52, §1 — multa de mora em contrato de credito limitada a 2%.",
        re.compile(r"\bmulta\b[^.]{0,40}\b([1-9]\d?)\s*%", re.IGNORECASE),
    ),
    (
        "juros_capitalizados",
        "alta",
        "Capitalizacao mensal de juros — exige pactuacao expressa (Sumula STJ 539).",
        re.compile(
            r"\b(capitaliza[çc][ãa]o|juros\s+sobre\s+juros|anatocismo)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "limitacao_reembolso",
        "media",
        "CDC Art. 51, II — limitacao de reembolso de valores ja pagos.",
        re.compile(
            r"\b(n[ãa]o\s+(?:haver[áa]|ser[áa])\s+(?:devolu|reembols)|"
            r"perda\s+(?:total|integral)\s+das?\s+(?:parcelas|quantias))",
            re.IGNORECASE,
        ),
    ),
    (
        "eleicao_arbitragem_compulsoria",
        "media",
        "CDC Art. 51, VII — arbitragem compulsoria imposta ao consumidor.",
        re.compile(r"\barbitragem\b[^.]{0,40}\b(obrigat[óo]ria|compuls[óo]ria)", re.IGNORECASE),
    ),
)

_FORO_ADESAO_RE = re.compile(
    r"\b(?:ele[iç][çc]?[ãa]o\s+de\s+foro|eleit[oa]\s+o\s+foro|foro\s+de\s+ele[iç][çc]?[ãa]o)\b",
    re.IGNORECASE,
)
_ADESAO_RE = re.compile(r"\bcontrato\s+de\s+ades[ãa]o\b", re.IGNORECASE)


def _trecho(text: str, start: int, end: int) -> str:
    ini = max(0, start - 20)
    fim = min(len(text), end + _TRECHO_JANELA)
    return text[ini:fim].strip()


def scan_clausulas_abusivas(text: str) -> tuple[ClausulaAbusiva, ...]:
    """Detecta clausulas abusivas via CDC Art. 51 e jurisprudencia correlata.

    Args:
        text: Texto do contrato (ja sem PII bruto).

    Returns:
        Tupla de ``ClausulaAbusiva`` encontradas (vazia se nenhuma).
    """
    if not text or not text.strip():
        return ()

    achados: list[ClausulaAbusiva] = []
    for tipo, severidade, fundamento, pattern in _CLAUSULA_PATTERNS:
        m = pattern.search(text)
        if m is None:
            continue
        if tipo == "multa_excessiva":
            try:
                pct = int(m.group(1))
            except (ValueError, IndexError):
                pct = 0
            if pct <= 2:
                continue
        achados.append(
            ClausulaAbusiva(
                tipo=tipo,
                severidade=severidade,
                fundamento=fundamento,
                trecho=_trecho(text, m.start(), m.end()),
            )
        )

    # Foro de eleicao em contrato de adesao: abusivo se dificulta defesa (CDC Art. 51, IV).
    if _FORO_ADESAO_RE.search(text) and _ADESAO_RE.search(text):
        m = _FORO_ADESAO_RE.search(text)
        assert m is not None
        achados.append(
            ClausulaAbusiva(
                tipo="foro_eleicao_adesao",
                severidade="baixa",
                fundamento="CDC Art. 51, IV — foro de eleicao em adesao pode ser abusivo.",
                trecho=_trecho(text, m.start(), m.end()),
            )
        )
    return tuple(achados)


# --- Financiamento ---------------------------------------------------------

_SPREAD_RE = re.compile(r"\bspread\b[^%\d]{0,20}(\d{1,3}(?:[.,]\d{1,2})?)\s*%", re.IGNORECASE)
_TAXA_MENSAL_RE = re.compile(
    r"\b(?:taxa|juros)\b[^%\d]{0,30}(\d{1,3}(?:[.,]\d{1,2})?)\s*%\s*(?:a\.?\s*m\.?|ao\s+m[êe]s)",
    re.IGNORECASE,
)
_INDEXADOR_RE = re.compile(
    r"\b(CDI|SELIC|IPCA|IGP-?M|INPC|TR|TJLP)\b",
    re.IGNORECASE,
)
_CAPITALIZACAO_RE = re.compile(
    r"\b(capitaliza[çc][ãa]o\s+mensal|juros\s+sobre\s+juros|anatocismo)\b",
    re.IGNORECASE,
)
_IOF_RE = re.compile(r"\bIOF\b", re.IGNORECASE)


def _to_float(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", ".")) if "," in raw else float(raw)


def analisar_financiamento(text: str) -> AnaliseFinanciamento:
    """Extrai parametros de um contrato de financiamento/credito.

    Args:
        text: Texto do contrato.

    Returns:
        ``AnaliseFinanciamento`` com spread, indexador, capitalizacao e alertas.
    """
    alertas: list[str] = []
    spread: float | None = None
    taxa_mensal: float | None = None
    indexador: str | None = None

    m = _SPREAD_RE.search(text)
    if m is not None:
        spread = _to_float(m.group(1))
        if spread > 30:
            alertas.append("Spread acima de 30% — revisar onerosidade excessiva (CDC Art. 51, IV).")

    m = _TAXA_MENSAL_RE.search(text)
    if m is not None:
        taxa_mensal = _to_float(m.group(1))

    mi = _INDEXADOR_RE.search(text)
    if mi is not None:
        indexador = mi.group(1).upper()

    capitalizacao = _CAPITALIZACAO_RE.search(text) is not None
    if capitalizacao:
        alertas.append(
            "Capitalizacao mensal de juros — exige pactuacao expressa (Sumula STJ 539/541)."
        )

    iof = _IOF_RE.search(text) is not None

    return AnaliseFinanciamento(
        spread_pct=spread,
        taxa_juros_mensal_pct=taxa_mensal,
        indexador=indexador,
        capitalizacao_mensal=capitalizacao,
        iof_presente=iof,
        alertas=tuple(alertas),
    )


# --- NDA review ------------------------------------------------------------

_NDA_PRAZO_RE = re.compile(
    r"\b(?:prazo|vig[êe]ncia|confidencialidade)\b[^.\d]{0,40}(\d{1,3})\s*(ano|anos|mes|meses)",
    re.IGNORECASE,
)
_NDA_PENALIDADE_RE = re.compile(r"\b(multa|penalidade|indeniza[çc][ãa]o)\b", re.IGNORECASE)
_NDA_ESCOPO_RE = re.compile(
    r"\b(informa[çc][õo]es?\s+confidenciais?|dados\s+confidenciais?)\b", re.IGNORECASE
)


def scan_nda(text: str) -> tuple[str, ...]:
    """Revisa um NDA e retorna lista de observacoes/pendencias.

    Args:
        text: Texto do acordo de confidencialidade.

    Returns:
        Tupla de strings com observacoes (vazia se NDA completo).
    """
    obs: list[str] = []
    if not text or not text.strip():
        return ("NDA vazio ou ilegivel.",)

    if _NDA_ESCOPO_RE.search(text) is None:
        obs.append("Escopo de 'informacoes confidenciais' nao definido explicitamente.")

    m = _NDA_PRAZO_RE.search(text)
    if m is None:
        obs.append("Prazo de confidencialidade ausente — recomenda-se definir vigencia.")
    else:
        unidade = m.group(2).lower()
        qtd = int(m.group(1))
        anos = qtd if unidade.startswith("ano") else qtd / 12
        if anos > 5:
            obs.append("Prazo de confidencialidade superior a 5 anos — avaliar razoabilidade.")

    if _NDA_PENALIDADE_RE.search(text) is None:
        obs.append("Penalidade por violacao nao prevista — clausula de multa recomendada.")

    return tuple(obs)


# --- Relatorio consolidado -------------------------------------------------


def analisar_contrato(text: str) -> RelatorioRisco:
    """Analisa um contrato e devolve um relatorio de risco pontuado.

    O score soma o peso das clausulas abusivas (baixa=1, media=3, alta=5) mais
    1 ponto por alerta de financiamento. Niveis: <=2 baixo, <=7 medio, >7 alto.

    Args:
        text: Texto do contrato (ja sem PII bruto).

    Returns:
        ``RelatorioRisco`` com clausulas, analise de financiamento e recomendacoes.
    """
    rel = RelatorioRisco()
    if not text or not text.strip():
        rel.recomendacoes.append("Contrato vazio ou ilegivel — nada a analisar.")
        return rel

    rel.clausulas = list(scan_clausulas_abusivas(text))
    fin = analisar_financiamento(text)
    if any(
        (
            fin.spread_pct is not None,
            fin.indexador is not None,
            fin.capitalizacao_mensal,
            fin.iof_presente,
        )
    ):
        rel.financiamento = fin

    score = sum(_SEVERIDADE_PESO[c.severidade] for c in rel.clausulas)
    if rel.financiamento is not None:
        score += len(rel.financiamento.alertas)
    rel.score = score
    rel.nivel = "baixo" if score <= 2 else ("medio" if score <= 7 else "alto")

    for clausula in rel.clausulas:
        rel.recomendacoes.append(f"Revisar clausula '{clausula.tipo}': {clausula.fundamento}")
    if rel.financiamento is not None:
        rel.recomendacoes.extend(rel.financiamento.alertas)
    if not rel.recomendacoes:
        rel.recomendacoes.append("Nenhuma clausula abusiva detectada nos padroes cobertos.")

    return rel
