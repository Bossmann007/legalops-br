"""Parser de emails do TJRJ (PJe RJ + sistema TJRJ).

Reusa engine do tjsp_parser (PJe similar formato).
"""

from __future__ import annotations

from legalops.tjpr_parser import Intimacao, TipoAto
from legalops.tjsp_parser import ParseResult, parse_email

__all__ = ["Intimacao", "ParseResult", "TipoAto", "parse_email"]
