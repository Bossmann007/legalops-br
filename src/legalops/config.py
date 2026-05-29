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

    [whatsapp]
    chat_id = "5541999999999@s.whatsapp.net"
    bridge_url = "http://localhost:3000"
    timeout = 10.0

Uso:
    from legalops.config import load_config
    cfg = load_config()
    print(cfg.whatsapp_chat_id)
"""

from __future__ import annotations

import os
import stat
import tomllib
import warnings
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Literal

DEFAULT_CONFIG_PATH = Path("~/.config/legalops/config.toml")

#: Env var que sobrepoe email.password do TOML (preferida — evita segredo em disco).
SMTP_PASSWORD_ENV = "LEGALOPS_SMTP_PASSWORD"  # noqa: S105 — env var name, not a secret

ParteType = Literal["particular", "fazenda", "mp", "defensoria"]


@dataclass(frozen=True)
class LegalOpsConfig:
    """Resolved config — todos os defaults aplicados."""

    parte: ParteType = "particular"
    via_dje: bool = False
    tribunal: str = "TJPR"
    audit_db: str | None = None
    whatsapp_chat_id: str | None = None
    whatsapp_bridge_url: str = "http://localhost:3000"
    whatsapp_timeout: float = 10.0
    # Email (v1.3)
    email_smtp_host: str | None = None
    email_smtp_port: int = 587
    email_username: str | None = None
    email_password: str | None = None
    email_from_addr: str | None = None
    email_to_addr: str | None = None
    email_use_tls: bool = True
    # Slack (v1.3)
    slack_webhook_url: str | None = None
    slack_channel: str = ""
    # Notification multiplex (v1.3)
    notification_channels: tuple[str, ...] = field(default_factory=tuple)
    notification_min_prazo_days: int = 3
    notification_quiet_start: time | None = None
    notification_quiet_end: time | None = None
    source_path: str | None = None


def _expand(value: object) -> object:
    """Expande ~ e $VAR em valores string."""
    if isinstance(value, str):
        return os.path.expandvars(os.path.expanduser(value))
    return value


def _resolve_smtp_password(cfg_value: object) -> str | None:
    """Resolve a senha SMTP: env ``LEGALOPS_SMTP_PASSWORD`` tem precedencia.

    Fallback para o valor do TOML (com expansao de ``$VAR``). Preferir env evita
    manter segredo em disco em texto plano.
    """
    env = os.environ.get(SMTP_PASSWORD_ENV)
    if env:
        return env
    if cfg_value is None:
        return None
    return str(_expand(cfg_value))


def _warn_if_world_readable(target: Path, data: dict[str, object]) -> None:
    """Avisa se o config tem senha em texto plano e permissoes frouxas (grupo/outros)."""
    email_cfg = data.get("email")
    has_plaintext_pw = isinstance(email_cfg, dict) and bool(email_cfg.get("password"))
    if not has_plaintext_pw:
        return
    try:
        mode = target.stat().st_mode
    except OSError:
        return
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        warnings.warn(
            f"{target} contem email.password em texto plano e e legivel por "
            f"grupo/outros (modo {stat.S_IMODE(mode):04o}). Restrinja com "
            f"`chmod 600 {target}` ou use {SMTP_PASSWORD_ENV}.",
            stacklevel=2,
        )


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

    _warn_if_world_readable(target, data)

    defaults = data.get("defaults", {})
    audit = data.get("audit", {})
    whatsapp = data.get("whatsapp", {})
    email_cfg = data.get("email", {})
    slack_cfg = data.get("slack", {})
    notif_cfg = data.get("notification", {})

    parte_raw = defaults.get("parte", "particular")
    if parte_raw not in ("particular", "fazenda", "mp", "defensoria"):
        raise ValueError(f"parte invalida em config: {parte_raw!r}")

    audit_db_raw = audit.get("db")
    audit_db = str(_expand(audit_db_raw)) if audit_db_raw else None

    def _parse_hhmm(raw: object) -> time | None:
        if not raw:
            return None
        if not isinstance(raw, str):
            raise ValueError(f"hora deve ser string HH:MM: {raw!r}")
        try:
            hh, mm = raw.split(":")
            return time(int(hh), int(mm))
        except (ValueError, IndexError) as e:
            raise ValueError(f"formato HH:MM invalido: {raw!r}") from e

    channels_raw = notif_cfg.get("channels", [])
    if not isinstance(channels_raw, list):
        raise ValueError(f"notification.channels deve ser lista: {channels_raw!r}")

    return LegalOpsConfig(
        parte=parte_raw,
        via_dje=bool(defaults.get("via_dje", False)),
        tribunal=str(defaults.get("tribunal", "TJPR")),
        audit_db=audit_db,
        whatsapp_chat_id=whatsapp.get("chat_id"),
        whatsapp_bridge_url=str(whatsapp.get("bridge_url", "http://localhost:3000")),
        whatsapp_timeout=float(whatsapp.get("timeout", 10.0)),
        email_smtp_host=email_cfg.get("smtp_host"),
        email_smtp_port=int(email_cfg.get("smtp_port", 587)),
        email_username=email_cfg.get("username"),
        email_password=_resolve_smtp_password(email_cfg.get("password")),
        email_from_addr=email_cfg.get("from_addr"),
        email_to_addr=email_cfg.get("to_addr"),
        email_use_tls=bool(email_cfg.get("use_tls", True)),
        slack_webhook_url=slack_cfg.get("webhook_url"),
        slack_channel=str(slack_cfg.get("channel", "")),
        notification_channels=tuple(str(c) for c in channels_raw),
        notification_min_prazo_days=int(notif_cfg.get("min_prazo_days", 3)),
        notification_quiet_start=_parse_hhmm(notif_cfg.get("quiet_start")),
        notification_quiet_end=_parse_hhmm(notif_cfg.get("quiet_end")),
        source_path=str(target),
    )
