"""Parser de emails do TJSC (e-Proc Tribunal de Justica de Santa Catarina).

Reusa engine do tjsp_parser (e-SAJ similar formato), delega parse_email.
Detector mapeia dominio + header.
"""

from __future__ import annotations

from legalops.tjpr_parser import Intimacao, TipoAto
from legalops.tjsp_parser import ParseResult, parse_email

__all__ = ["Intimacao", "ParseResult", "TipoAto", "parse_email"]
