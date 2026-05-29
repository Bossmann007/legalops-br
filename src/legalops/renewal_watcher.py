"""Renewal Watcher — monitor de vencimento de contratos (fase v1.2 do roadmap).

Acompanha contratos do escritorio e emite alertas quando se aproxima:
- a data de vencimento, ou
- a data limite para enviar aviso previo de nao-renovacao.

Deterministico, stdlib only. Nenhuma PII nos metadados (apenas id + descricao
curta + datas). Nao loga conteudo de contrato.

Uso:
    >>> from datetime import date
    >>> from legalops.renewal_watcher import Contrato, RenewalWatcher
    >>> w = RenewalWatcher()
    >>> w.add(Contrato("c1", "Locacao sala", date(2026, 1, 1), date(2026, 6, 30), 30))
    >>> alertas = w.check(hoje=date(2026, 6, 20))
    >>> alertas[0].urgencia
    'critico'
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

__all__ = ["AlertaRenovacao", "Contrato", "RenewalWatcher", "Urgencia"]

Urgencia = Literal["vencido", "critico", "atencao", "ok"]

# Limiares (dias) para classificar urgencia a partir do evento mais proximo
# (vencimento ou prazo de aviso previo).
_CRITICO_DIAS = 15
_ATENCAO_DIAS = 45


@dataclass(frozen=True)
class Contrato:
    """Um contrato monitorado.

    Attributes:
        contrato_id: Identificador opaco (sem PII).
        descricao: Descricao curta (sem PII).
        data_inicio: Inicio da vigencia.
        data_fim: Fim da vigencia.
        aviso_previo_dias: Antecedencia minima para avisar nao-renovacao.
        renovacao_automatica: Se renova automaticamente sem manifestacao.
    """

    contrato_id: str
    descricao: str
    data_inicio: date
    data_fim: date
    aviso_previo_dias: int = 0
    renovacao_automatica: bool = False


@dataclass(frozen=True)
class AlertaRenovacao:
    """Alerta emitido para um contrato proximo de evento relevante."""

    contrato_id: str
    descricao: str
    data_fim: date
    dias_para_vencimento: int
    dias_para_aviso: int | None
    urgencia: Urgencia
    renovacao_automatica: bool


def _classificar(dias_evento: int) -> Urgencia:
    if dias_evento < 0:
        return "vencido"
    if dias_evento <= _CRITICO_DIAS:
        return "critico"
    if dias_evento <= _ATENCAO_DIAS:
        return "atencao"
    return "ok"


_ORDEM: dict[Urgencia, int] = {"vencido": 0, "critico": 1, "atencao": 2, "ok": 3}


class RenewalWatcher:
    """Registra contratos e calcula alertas de renovacao numa data de referencia."""

    def __init__(self) -> None:
        self._contratos: dict[str, Contrato] = {}

    def add(self, contrato: Contrato) -> None:
        """Adiciona (ou substitui) um contrato pelo ``contrato_id``."""
        self._contratos[contrato.contrato_id] = contrato

    def remove(self, contrato_id: str) -> None:
        """Remove um contrato monitorado, se existir."""
        self._contratos.pop(contrato_id, None)

    def contratos(self) -> list[Contrato]:
        """Lista contratos monitorados (ordem de insercao)."""
        return list(self._contratos.values())

    def _alerta(self, contrato: Contrato, hoje: date) -> AlertaRenovacao:
        dias_venc = (contrato.data_fim - hoje).days
        dias_aviso: int | None = None
        evento = dias_venc
        if contrato.aviso_previo_dias > 0:
            from datetime import timedelta

            data_aviso = contrato.data_fim - timedelta(days=contrato.aviso_previo_dias)
            dias_aviso = (data_aviso - hoje).days
            # O evento mais proximo (aviso previo vence antes do contrato) define a urgencia.
            evento = min(dias_venc, dias_aviso)
        return AlertaRenovacao(
            contrato_id=contrato.contrato_id,
            descricao=contrato.descricao,
            data_fim=contrato.data_fim,
            dias_para_vencimento=dias_venc,
            dias_para_aviso=dias_aviso,
            urgencia=_classificar(evento),
            renovacao_automatica=contrato.renovacao_automatica,
        )

    def check(self, hoje: date | None = None, incluir_ok: bool = False) -> list[AlertaRenovacao]:
        """Calcula alertas para a data de referencia.

        Args:
            hoje: Data de referencia (default: ``date.today()``).
            incluir_ok: Se ``True``, inclui contratos com urgencia ``ok``.

        Returns:
            Lista de ``AlertaRenovacao`` ordenada por urgencia (mais urgente
            primeiro) e, em empate, por data de vencimento.
        """
        ref = hoje if hoje is not None else date.today()
        alertas = [self._alerta(c, ref) for c in self._contratos.values()]
        if not incluir_ok:
            alertas = [a for a in alertas if a.urgencia != "ok"]
        alertas.sort(key=lambda a: (_ORDEM[a.urgencia], a.data_fim))
        return alertas
