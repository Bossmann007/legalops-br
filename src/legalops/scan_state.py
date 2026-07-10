"""Estado da última varredura de caixa — a lógica "não-olhei ≠ nada-novo".

Determinístico, zero-token. Guarda quando foi a última leitura da caixa e o
resultado, para que o painel/briefing nunca renderizem ausência de prazos como
"nada novo" sem qualificar a última leitura bem-sucedida.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

SCAN_STATE_PATH = Path("state/scan-state.json")


@dataclass
class ScanState:
    ultima_varredura: str | None  # ISO 8601 local, None se nunca varreu
    resultado: str  # "ok" | "vazio" | "falha"
    n_encontrados: int = 0
    n_processados: int = 0
    n_revisao: int = 0


def describe_state(state: ScanState | None, *, hoje: date) -> dict[str, object]:
    """Traduz o estado bruto em um dos 4 estados de UX + comando sugerido.

    Estados: "nunca" (nunca varreu OU última varredura foi antes de hoje),
    "ok", "vazio", "falha". Cada um carrega mensagem e o próximo `/`.
    """
    if state is None or not state.ultima_varredura:
        return {
            "estado": "nunca",
            "mensagem": "Você ainda não checou a caixa hoje.",
            "comando_sugerido": "/varrer",
        }

    varreu_em = date.fromisoformat(state.ultima_varredura[:10])
    if varreu_em < hoje:
        return {
            "estado": "nunca",
            "mensagem": f"Última varredura foi em {varreu_em.strftime('%d/%m')}. "
            "Você ainda não checou a caixa hoje.",
            "comando_sugerido": "/varrer",
        }

    hora = state.ultima_varredura[11:16]
    if state.resultado == "falha":
        return {
            "estado": "falha",
            "mensagem": "NÃO consegui olhar sua caixa (a conexão com o Outlook pode "
            "ter caído). NÃO assuma que não há prazo. Reconecte e rode /varrer de "
            "novo, ou cole a intimação no /intimacao.",
            "comando_sugerido": "/intimacao",
        }
    if state.resultado == "vazio":
        return {
            "estado": "vazio",
            "mensagem": f"Última varredura: hoje {hora} — nenhuma intimação nova na caixa.",
            "comando_sugerido": "/painel",
        }
    return {
        "estado": "ok",
        "mensagem": f"Última varredura: hoje {hora} ({state.n_encontrados} encontrados).",
        "comando_sugerido": "/painel",
    }


def load_scan_state(path: Path = SCAN_STATE_PATH) -> ScanState | None:
    """Lê o estado; None se o arquivo não existe."""
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ScanState(
        ultima_varredura=raw.get("ultima_varredura"),
        resultado=raw.get("resultado", "vazio"),
        n_encontrados=int(raw.get("n_encontrados", 0)),
        n_processados=int(raw.get("n_processados", 0)),
        n_revisao=int(raw.get("n_revisao", 0)),
    )


def save_scan_state(state: ScanState, path: Path = SCAN_STATE_PATH) -> None:
    """Grava o estado (cria o diretório se preciso)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
