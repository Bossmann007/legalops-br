"""Config file loader pra LegalOps CLI.

Le ~/.config/legalops/config.toml (XDG-style) com defaults pra subcomandos CLI.
Valores no config sao overridable por flags CLI.

Schema TOML:
    [defaults]
    parte = "particular"
    via_dje = false
    tribunal = "TJPR"

    [audit]
    db = "~/.local/share/legalops/audit.db"

Uso:
    from legalops.config import load_config
    cfg = load_config()
    print(cfg.audit_db)
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DEFAULT_CONFIG_PATH = Path("~/.config/legalops/config.toml")

ParteType = Literal["particular", "fazenda", "mp", "defensoria"]


@dataclass(frozen=True)
class LegalOpsConfig:
    """Resolved config — todos os defaults aplicados."""

    parte: ParteType = "particular"
    via_dje: bool = False
    tribunal: str = "TJPR"
    audit_db: str | None = None
    source_path: str | None = None


def _expand(value: object) -> object:
    """Expande ~ e $VAR em valores string."""
    if isinstance(value, str):
        return os.path.expandvars(os.path.expanduser(value))
    return value


def load_config(path: Path | None = None) -> LegalOpsConfig:
    """Carrega config TOML. Se path None, usa DEFAULT_CONFIG_PATH expanded.

    Se arquivo nao existe, retorna LegalOpsConfig() com defaults built-in.
    Erros de parsing TOML viram ValueError.
    """
    target = (path or DEFAULT_CONFIG_PATH).expanduser()

    if not target.exists():
        return LegalOpsConfig()

    try:
        with target.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Config TOML invalido em {target}: {e}") from e

    defaults = data.get("defaults", {})
    audit = data.get("audit", {})

    parte_raw = defaults.get("parte", "particular")
    if parte_raw not in ("particular", "fazenda", "mp", "defensoria"):
        raise ValueError(f"parte invalida em config: {parte_raw!r}")

    audit_db_raw = audit.get("db")
    audit_db = str(_expand(audit_db_raw)) if audit_db_raw else None

    return LegalOpsConfig(
        parte=parte_raw,
        via_dje=bool(defaults.get("via_dje", False)),
        tribunal=str(defaults.get("tribunal", "TJPR")),
        audit_db=audit_db,
        source_path=str(target),
    )
