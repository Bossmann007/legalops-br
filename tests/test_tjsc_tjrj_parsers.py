"""Tests para tjsc_parser (e-Proc) e tjrj_parser (PJe-RJ).

Cobrem: basic parse, vara, comarca, prazo, multi-process,
tipo_ato variantes, prazo peremptorio/sem prazo, encoding utf-8.
"""

from __future__ import annotations

from datetime import date

from legalops.orchestrator import process_email
from legalops.tjrj_parser import parse_email as parse_tjrj
from legalops.tjsc_parser import parse_email as parse_tjsc


class TestTJSC:
    def test_basic_parse(self) -> None:
        txt = "e-Proc TJSC\nAutos n. 1234567-89.2026.8.24.0001\nDespacho: prazo de 15 dias."
        r = parse_tjsc(txt)
        assert r.total == 1
        assert r.intimacoes[0].numero_processo == "1234567-89.2026.8.24.0001"
        assert r.intimacoes[0].prazo_dias == 15
        assert r.intimacoes[0].tipo_ato == "despacho"

    def test_vara_extraction(self) -> None:
        txt = (
            "Sistema e-Proc\n"
            "Autos no 1111111-11.2026.8.24.0023\n"
            "2a Vara Civel de Florianopolis\nDespacho: prazo de 5 dias."
        )
        r = parse_tjsc(txt)
        assert r.total == 1
        vara = r.intimacoes[0].vara or ""
        assert "Vara" in vara
        assert "Civel" in vara or "Cível" in vara

    def test_comarca_extraction(self) -> None:
        txt = (
            "Tribunal de Justica de Santa Catarina\n"
            "Processo eletronico: 2222222-22.2026.8.24.0023\n"
            "Foro da Comarca de Joinville.\nDespacho: prazo de 10 dias."
        )
        r = parse_tjsc(txt)
        assert r.total == 1
        assert r.intimacoes[0].comarca == "Joinville"

    def test_prazo_legal(self) -> None:
        txt = (
            "e-Proc\nAutos n. 3333333-33.2026.8.24.0023\n"
            "Decisao: prazo legal de 15 dias para recurso."
        )
        r = parse_tjsc(txt)
        assert r.intimacoes[0].prazo_dias == 15
        assert r.intimacoes[0].tipo_ato == "decisao"

    def test_prazo_manifestar_se(self) -> None:
        txt = (
            "e-Proc\nAutos n. 4444444-44.2026.8.24.0023\nIntimacao: manifestar-se em 5 dias uteis."
        )
        r = parse_tjsc(txt)
        assert r.intimacoes[0].prazo_dias == 5

    def test_multi_process(self) -> None:
        txt = (
            "e-Proc TJSC\n"
            "Autos n. 1000001-01.2026.8.24.0023\nDespacho: prazo de 5 dias.\n"
            "---\n"
            "Autos n. 1000002-02.2026.8.24.0023\nSentenca proferida. prazo de 15 dias."
        )
        r = parse_tjsc(txt)
        assert r.total == 2
        assert r.intimacoes[0].tipo_ato == "despacho"
        assert r.intimacoes[1].tipo_ato == "sentenca"

    def test_tipo_ato_sentenca(self) -> None:
        txt = (
            "e-Proc\nAutos n. 5555555-55.2026.8.24.0023\nSentenca de procedencia. prazo de 15 dias."
        )
        r = parse_tjsc(txt)
        assert r.intimacoes[0].tipo_ato == "sentenca"

    def test_tipo_ato_decisao(self) -> None:
        txt = "e-Proc\nAutos n. 6666666-66.2026.8.24.0023\nDecisao interlocutoria. prazo de 5 dias."
        r = parse_tjsc(txt)
        assert r.intimacoes[0].tipo_ato == "decisao"

    def test_sem_prazo(self) -> None:
        txt = "e-Proc\nAutos n. 7777777-77.2026.8.24.0023\nPublicacao para ciencia."
        r = parse_tjsc(txt)
        assert r.intimacoes[0].prazo_dias is None
        assert r.intimacoes[0].tipo_ato == "publicacao"

    def test_encoding_utf8_acentos(self) -> None:
        txt = (
            "e-Proc Tribunal de Justiça de Santa Catarina\n"
            "Autos n. 8888888-88.2026.8.24.0023\n"
            "Foro da Comarca de São José.\n"
            "Sentença: prazo de 15 dias para apelação."
        )
        r = parse_tjsc(txt)
        assert r.total == 1
        assert r.intimacoes[0].tipo_ato == "sentenca"
        assert r.intimacoes[0].comarca is not None
        assert "Jos" in r.intimacoes[0].comarca

    def test_orchestrator_routes_tjsc(self) -> None:
        txt = "e-Proc TJSC\nAutos n. 1234567-89.2026.8.24.0001\nDespacho: prazo de 10 dias."
        results = process_email(
            txt,
            parte="particular",
            hoje=date(2026, 5, 28),
            sender="eproc@tjsc.jus.br",
        )
        assert len(results) == 1


class TestTJRJ:
    def test_basic_parse(self) -> None:
        txt = (
            "PJe-RJ\nProcesso n. 1234567-89.2026.8.19.0001\n"
            "Sentenca: prazo de 15 dias para apelacao."
        )
        r = parse_tjrj(txt)
        assert r.total == 1
        assert r.intimacoes[0].numero_processo == "1234567-89.2026.8.19.0001"
        assert r.intimacoes[0].prazo_dias == 15
        assert r.intimacoes[0].tipo_ato == "sentenca"

    def test_vara_extraction(self) -> None:
        txt = (
            "PJe Rio de Janeiro\n"
            "Processo n. 1111111-11.2026.8.19.0001\n"
            "3a Vara Empresarial da Capital\nDespacho: prazo de 5 dias."
        )
        r = parse_tjrj(txt)
        vara = r.intimacoes[0].vara or ""
        assert "Vara" in vara
        assert "Empresarial" in vara

    def test_comarca_extraction(self) -> None:
        txt = (
            "Tribunal de Justica do Estado do Rio de Janeiro\n"
            "Processo numero: 2222222-22.2026.8.19.0001\n"
            "Comarca de Niteroi.\nDespacho: prazo de 10 dias."
        )
        r = parse_tjrj(txt)
        assert r.intimacoes[0].comarca == "Niteroi"

    def test_comarca_capital(self) -> None:
        txt = (
            "PJe-RJ\nAutos: 9999999-99.2026.8.19.0001\n"
            "Comarca da Capital.\nSentenca: prazo de 15 dias."
        )
        r = parse_tjrj(txt)
        assert r.intimacoes[0].comarca == "Capital"

    def test_prazo_no_prazo_legal(self) -> None:
        txt = (
            "PJe-RJ\nProcesso n. 3333333-33.2026.8.19.0001\n"
            "Decisao: recorrer no prazo legal de 15 dias."
        )
        r = parse_tjrj(txt)
        assert r.intimacoes[0].prazo_dias == 15
        assert r.intimacoes[0].tipo_ato == "decisao"

    def test_prazo_em_dias(self) -> None:
        txt = (
            "PJe-RJ\nProcesso n. 4444444-44.2026.8.19.0001\n"
            "Intimacao: cumprir a obrigacao em 5 dias uteis."
        )
        r = parse_tjrj(txt)
        assert r.intimacoes[0].prazo_dias == 5

    def test_multi_process(self) -> None:
        txt = (
            "PJe-RJ\n"
            "Processo n. 1000001-01.2026.8.19.0001\nDespacho: prazo de 5 dias.\n"
            "---\n"
            "Processo n. 1000002-02.2026.8.19.0001\nSentenca proferida. prazo de 15 dias."
        )
        r = parse_tjrj(txt)
        assert r.total == 2
        assert r.intimacoes[0].tipo_ato == "despacho"
        assert r.intimacoes[1].tipo_ato == "sentenca"

    def test_cartorio_legado(self) -> None:
        txt = (
            "Tribunal de Justica RJ\n"
            "Autos: 5555555-55.2026.8.19.0001\n"
            "5o Cartorio da Fazenda Publica\nDespacho: prazo de 10 dias."
        )
        r = parse_tjrj(txt)
        vara_or_cart = r.intimacoes[0].vara or ""
        assert "Cart" in vara_or_cart or "Vara" in vara_or_cart

    def test_tipo_ato_despacho(self) -> None:
        txt = "PJe-RJ\nProcesso n. 6666666-66.2026.8.19.0001\nDespacho saneador. prazo de 5 dias."
        r = parse_tjrj(txt)
        assert r.intimacoes[0].tipo_ato == "despacho"

    def test_sem_prazo(self) -> None:
        txt = "PJe-RJ\nProcesso n. 7777777-77.2026.8.19.0001\nPublicacao para ciencia."
        r = parse_tjrj(txt)
        assert r.intimacoes[0].prazo_dias is None
        assert r.intimacoes[0].tipo_ato == "publicacao"

    def test_encoding_utf8_acentos(self) -> None:
        txt = (
            "PJe-RJ Tribunal de Justiça do Estado do Rio de Janeiro\n"
            "Processo n. 8888888-88.2026.8.19.0001\n"
            "Comarca de Niterói.\n"
            "Sentença: prazo de 15 dias para apelação."
        )
        r = parse_tjrj(txt)
        assert r.total == 1
        assert r.intimacoes[0].tipo_ato == "sentenca"
        assert r.intimacoes[0].comarca is not None
        assert "Niter" in r.intimacoes[0].comarca

    def test_orchestrator_routes_tjrj(self) -> None:
        txt = (
            "PJe-RJ Tribunal de Justica do Rio de Janeiro\n"
            "Processo n. 1234567-89.2026.8.19.0001\n"
            "Decisao: prazo de 5 dias."
        )
        results = process_email(
            txt,
            parte="particular",
            hoje=date(2026, 5, 28),
            sender="pje@tjrj.jus.br",
        )
        assert len(results) == 1


class TestEdgeBranches:
    """Cobertura branches defensivos: empty, no CNJ, tipo desconhecido, data invalida."""

    def test_tjsc_empty_text(self) -> None:
        r = parse_tjsc("")
        assert r.total == 0
        assert "vazio" in r.erros[0].lower()

    def test_tjsc_whitespace_only(self) -> None:
        r = parse_tjsc("   \n\t  ")
        assert r.total == 0
        assert "vazio" in r.erros[0].lower()

    def test_tjsc_no_cnj_number(self) -> None:
        r = parse_tjsc("Email sem numero de processo, nada parsavel")
        assert r.total == 0
        assert any("cnj" in e.lower() for e in r.erros)

    def test_tjsc_tipo_desconhecido(self) -> None:
        # Texto com CNJ mas sem palavra-chave de tipo_ato
        txt = "e-Proc TJSC\nAutos n. 1234567-89.2026.8.24.0001\nXXX YYY ZZZ unknown.\n"
        r = parse_tjsc(txt)
        assert r.total == 1
        assert r.intimacoes[0].tipo_ato == "desconhecido"

    def test_tjsc_invalid_yyyymmdd_falls_through(self) -> None:
        # YYYYMMDD com mes=13 — regex casa, date() lanca ValueError, cai pra
        # DDMMYYYY ou retorna None.
        txt = (
            "e-Proc TJSC\n"
            "Data: 2026-13-45\n"
            "Autos n. 1234567-89.2026.8.24.0001\n"
            "Despacho prazo 10 dias.\n"
        )
        r = parse_tjsc(txt)
        assert r.total == 1
        # data_publicacao deveria ser None (regex casou mas date() falhou)
        # ou cair em DDMMYYYY parsing diferente
        # nao asseguramos o valor — so que nao crashou

    def test_tjsc_invalid_ddmmyyyy(self) -> None:
        # DDMMYYYY com mes=13 — regex casa, date() lanca ValueError
        txt = (
            "e-Proc TJSC\n"
            "Data: 45/13/2026\n"
            "Autos n. 1234567-89.2026.8.24.0001\n"
            "Despacho prazo 10 dias.\n"
        )
        r = parse_tjsc(txt)
        assert r.total == 1

    def test_tjrj_empty_text(self) -> None:
        r = parse_tjrj("")
        assert r.total == 0
        assert "vazio" in r.erros[0].lower()

    def test_tjrj_no_cnj(self) -> None:
        r = parse_tjrj("PJe-RJ sem processo")
        assert r.total == 0
        assert any("cnj" in e.lower() for e in r.erros)

    def test_tjrj_tipo_desconhecido(self) -> None:
        txt = "PJe-RJ\nProcesso n. 1234567-89.2026.8.19.0001\nXXX YYY conteudo neutro.\n"
        r = parse_tjrj(txt)
        assert r.total == 1
        assert r.intimacoes[0].tipo_ato == "desconhecido"

    def test_tjrj_invalid_dates(self) -> None:
        txt = (
            "PJe-RJ\n"
            "Data: 2026-13-99 ou 45/13/2026\n"
            "Processo n. 1234567-89.2026.8.19.0001\n"
            "Despacho prazo 10 dias.\n"
        )
        r = parse_tjrj(txt)
        assert r.total == 1

    def test_tjrj_cartorio_fallback_vara(self) -> None:
        # Fallback CARTORIO_RE quando nao tem VARA_RE match
        txt = (
            "PJe-RJ legado\n"
            "5o Cartorio Civel\n"
            "Processo n. 1234567-89.2026.8.19.0001\n"
            "Despacho prazo 5 dias.\n"
        )
        r = parse_tjrj(txt)
        assert r.total == 1
        # vara deveria vir de _extract_vara via cartorio fallback
        assert r.intimacoes[0].vara is not None
