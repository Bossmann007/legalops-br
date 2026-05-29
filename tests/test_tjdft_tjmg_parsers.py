"""Tests parsers TJDFT (e-SAJ) e TJMG (PJe-MG) — corpus sintetico."""

from __future__ import annotations

from datetime import date

from legalops.orchestrator import process_email
from legalops.tjdft_parser import parse_email as parse_tjdft
from legalops.tjmg_parser import parse_email as parse_tjmg


class TestTJDFTBasic:
    def test_empty_text(self) -> None:
        r = parse_tjdft("")
        assert r.total == 0
        assert "Texto vazio" in r.erros

    def test_no_cnj(self) -> None:
        r = parse_tjdft("Nenhum processo aqui apenas texto.")
        assert r.total == 0
        assert any("CNJ" in e for e in r.erros)

    def test_single_processo(self) -> None:
        text = "e-SAJ TJDFT\nProcesso n. 0123456-78.2024.8.07.0001\nDespacho."
        r = parse_tjdft(text)
        assert r.total == 1
        assert r.intimacoes[0].numero_processo == "0123456-78.2024.8.07.0001"

    def test_vara_extraction(self) -> None:
        text = "TJDFT\nProcesso 0001234-56.2024.8.07.0001\n2a Vara Civel de Brasilia"
        r = parse_tjdft(text)
        assert r.intimacoes[0].vara is not None
        assert "Vara" in r.intimacoes[0].vara

    def test_comarca_brasilia(self) -> None:
        text = "TJDFT 0001234-56.2024.8.07.0001\nComarca de Brasilia."
        r = parse_tjdft(text)
        assert r.intimacoes[0].comarca is not None
        assert "Bras" in r.intimacoes[0].comarca

    def test_comarca_circunscricao(self) -> None:
        text = "TJDFT 0001234-56.2024.8.07.0001\nCircunscricao Especial de Brasilia."
        r = parse_tjdft(text)
        assert r.intimacoes[0].comarca is not None
        assert "Circunscri" in r.intimacoes[0].comarca

    def test_prazo_dias(self) -> None:
        text = "TJDFT 0001234-56.2024.8.07.0001\nIntime-se a parte para manifestar-se em 15 dias."
        r = parse_tjdft(text)
        assert r.intimacoes[0].prazo_dias == 15

    def test_prazo_legal(self) -> None:
        text = "TJDFT 0001234-56.2024.8.07.0001\nNo prazo legal de 5 dias."
        r = parse_tjdft(text)
        assert r.intimacoes[0].prazo_dias == 5

    def test_multi_processo(self) -> None:
        text = (
            "e-SAJ TJDFT\n"
            "Processo 0000001-11.2024.8.07.0001 despacho.\n"
            "Processo 0000002-22.2024.8.07.0002 sentenca."
        )
        r = parse_tjdft(text)
        assert r.total == 2
        assert r.intimacoes[1].tipo_ato == "sentenca"

    def test_tipo_ato_decisao(self) -> None:
        text = "TJDFT 0001234-56.2024.8.07.0001 Decisao publicada."
        r = parse_tjdft(text)
        assert r.intimacoes[0].tipo_ato == "decisao"

    def test_utf8_encoding(self) -> None:
        text = (
            "Tribunal de Justiça do Distrito Federal\n"
            "Processo 0001234-56.2024.8.07.0001\n"
            "Cível — Brasília — intimação."
        )
        r = parse_tjdft(text)
        assert r.total == 1
        assert r.intimacoes[0].tipo_ato == "intimacao"

    def test_data_publicacao(self) -> None:
        text = "TJDFT 0001234-56.2024.8.07.0001 publicado em 15/03/2024."
        r = parse_tjdft(text)
        assert r.intimacoes[0].data_publicacao == date(2024, 3, 15)

    def test_orchestrator_routes_tjdft(self) -> None:
        text = (
            "e-SAJ TJDFT\nProcesso 0001234-56.2024.8.07.0001\n"
            "Intime-se em 15 dias. Publicado em 15/03/2024."
        )
        results = process_email(text, sender="naoresponda@tjdft.jus.br")
        assert len(results) == 1
        assert results[0].numero_processo == "0001234-56.2024.8.07.0001"


class TestTJMGBasic:
    def test_empty_text(self) -> None:
        r = parse_tjmg("")
        assert r.total == 0
        assert "Texto vazio" in r.erros

    def test_no_cnj(self) -> None:
        r = parse_tjmg("Texto sem CNJ.")
        assert r.total == 0

    def test_single_processo(self) -> None:
        text = "PJe TJMG\nProcesso: 0123456-78.2024.8.13.0024\nDespacho."
        r = parse_tjmg(text)
        assert r.total == 1
        assert r.intimacoes[0].numero_processo == "0123456-78.2024.8.13.0024"

    def test_vara_extraction(self) -> None:
        text = "PJe-MG 0001234-56.2024.8.13.0024\n3a Vara Civel de Belo Horizonte"
        r = parse_tjmg(text)
        assert r.intimacoes[0].vara is not None
        assert "Vara" in r.intimacoes[0].vara

    def test_comarca_bh(self) -> None:
        text = "PJe TJMG 0001234-56.2024.8.13.0024\nComarca de Belo Horizonte."
        r = parse_tjmg(text)
        assert r.intimacoes[0].comarca == "Belo Horizonte"

    def test_comarca_outras_cidades(self) -> None:
        text = "PJe-MG 0001234-56.2024.8.13.0672\nComarca de Uberlandia."
        r = parse_tjmg(text)
        assert r.intimacoes[0].comarca == "Uberlandia"

    def test_prazo_em_dias(self) -> None:
        text = "PJe TJMG 0001234-56.2024.8.13.0024\nManifestar-se em 10 dias."
        r = parse_tjmg(text)
        assert r.intimacoes[0].prazo_dias == 10

    def test_prazo_no_prazo_de(self) -> None:
        text = "PJe TJMG 0001234-56.2024.8.13.0024\nNo prazo de 15 dias."
        r = parse_tjmg(text)
        assert r.intimacoes[0].prazo_dias == 15

    def test_multi_processo(self) -> None:
        text = (
            "Tribunal de Justica de Minas Gerais\n"
            "Processo: 0000001-11.2024.8.13.0024 sentenca.\n"
            "Processo: 0000002-22.2024.8.13.0672 despacho."
        )
        r = parse_tjmg(text)
        assert r.total == 2

    def test_tipo_ato_sentenca(self) -> None:
        text = "PJe-MG 0001234-56.2024.8.13.0024 Sentenca proferida."
        r = parse_tjmg(text)
        assert r.intimacoes[0].tipo_ato == "sentenca"

    def test_utf8_encoding(self) -> None:
        text = (
            "Tribunal de Justiça de Minas Gerais\n"
            "Processo: 0001234-56.2024.8.13.0024\n"
            "Cível — intimação no prazo de 5 dias."
        )
        r = parse_tjmg(text)
        assert r.total == 1
        assert r.intimacoes[0].prazo_dias == 5

    def test_data_publicacao(self) -> None:
        text = "PJe TJMG 0001234-56.2024.8.13.0024 publicado em 20/04/2024."
        r = parse_tjmg(text)
        assert r.intimacoes[0].data_publicacao == date(2024, 4, 20)

    def test_orchestrator_routes_tjmg(self) -> None:
        text = (
            "PJe TJMG\nProcesso: 0001234-56.2024.8.13.0024\n"
            "Comarca de Belo Horizonte. Em 10 dias. Publicado em 10/02/2024."
        )
        results = process_email(text, sender="naoresponda@tjmg.jus.br")
        assert len(results) == 1
        assert results[0].numero_processo == "0001234-56.2024.8.13.0024"
