"""Filtro de triagem: quais emails são candidatos a intimação de tribunal.

Puro e determinístico. Reusa `detect_tribunal`. Não faz rede nem cálculo de
prazo — só separa o que vale a pena mandar pro pipeline do que é ruído.
"""

from __future__ import annotations

from datetime import date, timedelta

from legalops.tribunal_detector import detect_tribunal


def filtrar_candidatos(
    emails: list[dict[str, object]],
    *,
    janela_dias: int,
    hoje: date,
) -> list[dict[str, object]]:
    """Devolve os emails de tribunal dentro da janela, com o tribunal marcado.

    Cada email de entrada: {sender, subject, data (ISO), body}.
    Cada candidato de saída acrescenta: {tribunal, data_suspeita}.
    Data ilegível NÃO descarta o email — marca `data_suspeita=True` para
    conferência (não olhei ≠ nada novo, aplicado ao nível do item).
    """
    limite = hoje - timedelta(days=janela_dias)
    candidatos: list[dict[str, object]] = []
    for e in emails:
        tribunal = detect_tribunal(str(e.get("body", "")), str(e.get("sender", "")))
        if tribunal == "unknown":
            continue

        data_suspeita = False
        try:
            data_email = date.fromisoformat(str(e.get("data", "")))
            if data_email < limite:
                continue
        except (TypeError, ValueError):
            data_suspeita = True  # não descarta: entra para conferência

        candidatos.append({**e, "tribunal": tribunal, "data_suspeita": data_suspeita})
    return candidatos
