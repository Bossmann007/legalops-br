"""Tests para config loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from legalops.config import DEFAULT_CONFIG_PATH, LegalOpsConfig, load_config


class TestDefaults:
    def test_no_file_returns_defaults(self, tmp_path: Path) -> None:
        cfg = load_config(tmp_path / "nao_existe.toml")
        assert cfg.parte == "particular"
        assert cfg.via_dje is False
        assert cfg.tribunal == "TJPR"
        assert cfg.audit_db is None
        assert cfg.whatsapp_chat_id is None
        assert cfg.whatsapp_bridge_url == "http://localhost:3000"
        assert cfg.whatsapp_timeout == 10.0
        assert cfg.source_path is None

    def test_default_path_constant(self) -> None:
        assert str(DEFAULT_CONFIG_PATH) == "~/.config/legalops/config.toml"


class TestLoadFromFile:
    def test_full_config(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
            [defaults]
            parte = "fazenda"
            via_dje = true
            tribunal = "STJ"

            [audit]
            db = "/var/lib/legalops/audit.db"

            [whatsapp]
            chat_id = "5541999999999@s.whatsapp.net"
            bridge_url = "http://bridge.local:3000"
            timeout = 15.0
            """
        )
        cfg = load_config(cfg_file)
        assert cfg.parte == "fazenda"
        assert cfg.via_dje is True
        assert cfg.tribunal == "STJ"
        assert cfg.audit_db == "/var/lib/legalops/audit.db"
        assert cfg.whatsapp_chat_id == "5541999999999@s.whatsapp.net"
        assert cfg.whatsapp_bridge_url == "http://bridge.local:3000"
        assert cfg.whatsapp_timeout == 15.0
        assert cfg.source_path == str(cfg_file)

    def test_partial_config_keeps_defaults(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
            [defaults]
            parte = "mp"
            """
        )
        cfg = load_config(cfg_file)
        assert cfg.parte == "mp"
        assert cfg.via_dje is False
        assert cfg.tribunal == "TJPR"

    def test_audit_db_expands_tilde(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
            [audit]
            db = "~/audit.db"
            """
        )
        cfg = load_config(cfg_file)
        assert cfg.audit_db is not None
        assert cfg.audit_db == str(tmp_path / "audit.db")

    def test_audit_db_expands_envvar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LEGALOPS_DATA", "/var/legalops")
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
            [audit]
            db = "$LEGALOPS_DATA/audit.db"
            """
        )
        cfg = load_config(cfg_file)
        assert cfg.audit_db == "/var/legalops/audit.db"

    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "empty.toml"
        cfg_file.write_text("")
        cfg = load_config(cfg_file)
        assert cfg.parte == "particular"
        assert cfg.source_path == str(cfg_file)


class TestValidation:
    def test_invalid_toml_raises(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "bad.toml"
        cfg_file.write_text("[unclosed section\n")
        with pytest.raises(ValueError, match="TOML invalido"):
            load_config(cfg_file)

    def test_invalid_parte_raises(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
            [defaults]
            parte = "ufo"
            """
        )
        with pytest.raises(ValueError, match="parte invalida"):
            load_config(cfg_file)


class TestStructure:
    def test_is_frozen(self) -> None:
        cfg = LegalOpsConfig()
        with pytest.raises(Exception):  # noqa: B017
            cfg.parte = "fazenda"  # type: ignore[misc]
