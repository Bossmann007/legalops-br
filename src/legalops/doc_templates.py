"""Renderizacao de documentos juridicos padrao a partir de campos extraidos.

Preenche templates pt-BR de procuracao e contrato de honorarios usando os
dataclasses de ``doc_extractor``. Campos ausentes sao marcados claramente como
``[A PREENCHER: <campo>]``. Nunca lanca excecao em campo ausente. Nao loga
conteudo.

Uso:
    >>> from legalops.doc_extractor import extract_procuracao
    >>> from legalops.doc_templates import render_procuracao
    >>> campos = extract_procuracao("Outorgante: ACME LTDA.")
    >>> "PROCURACAO" in render_procuracao(campos).upper()
    True
"""

from __future__ import annotations

from legalops.doc_extractor import ContratoHonorariosCampos, ProcuracaoCampos

__all__ = ["render_contrato_honorarios", "render_procuracao"]

_PODERES_TEXTO: dict[str, str] = {
    "ad_judicia": (
        "para o foro em geral, com a clausula ad judicia, podendo propor "
        "acoes, contestar, recorrer e praticar todos os atos necessarios ao "
        "bom e fiel cumprimento deste mandato"
    ),
    "ad_judicia_et_extra": (
        "para o foro em geral, com as clausulas ad judicia et extra, podendo "
        "atuar judicial e extrajudicialmente, propor e acompanhar acoes, "
        "recorrer e praticar todos os atos necessarios ao mandato"
    ),
    "especiais": (
        "com poderes especiais para transigir, alienar, firmar acordos, "
        "receber e dar quitacao, alem dos poderes da clausula ad judicia"
    ),
    "desconhecido": "[A PREENCHER: poderes]",
}

_FORMA_PAGAMENTO_TEXTO: dict[str, str] = {
    "a_vista": "O pagamento sera efetuado a vista.",
    "parcelado": "O pagamento sera efetuado de forma parcelada.",
    "exito": "Os honorarios serao devidos a titulo de exito sobre o proveito economico.",
    "misto": (
        "O pagamento combina parcela fixa e honorarios de exito sobre o proveito economico obtido."
    ),
    "desconhecido": "[A PREENCHER: forma_pagamento]",
}


def _placeholder(value: str | None, campo: str) -> str:
    if value is None or not value.strip():
        return f"[A PREENCHER: {campo}]"
    return value.strip()


def render_procuracao(campos: ProcuracaoCampos) -> str:
    """Renderiza uma procuracao em pt-BR a partir dos campos extraidos.

    Args:
        campos: Campos extraidos da procuracao.

    Returns:
        Texto da procuracao preenchido. Campos ausentes aparecem como
        ``[A PREENCHER: <campo>]``. Nunca lanca excecao.
    """
    outorgante = _placeholder(campos.outorgante, "outorgante")
    outorgado = _placeholder(campos.outorgado, "outorgado")
    comarca = _placeholder(campos.comarca, "comarca")
    poderes = _PODERES_TEXTO.get(campos.poderes, _PODERES_TEXTO["desconhecido"])

    if campos.oab and campos.oab.strip():
        oab_linha = f", inscrito(a) na OAB sob o n. {campos.oab.strip()}"
    else:
        oab_linha = ""

    data = campos.data.strftime("%d/%m/%Y") if campos.data else "[A PREENCHER: data]"

    return (
        "PROCURACAO\n\n"
        f"OUTORGANTE: {outorgante}.\n\n"
        f"OUTORGADO: {outorgado}{oab_linha}.\n\n"
        "Pelo presente instrumento particular de procuracao, o(a) outorgante "
        f"nomeia e constitui seu(sua) bastante procurador(a) o(a) outorgado(a), "
        f"{poderes}, perante a Comarca de {comarca}.\n\n"
        f"Local e data: {comarca}, {data}.\n\n"
        "______________________________\n"
        f"{outorgante}\n"
    )


def render_contrato_honorarios(campos: ContratoHonorariosCampos) -> str:
    """Renderiza um contrato de honorarios em pt-BR a partir dos campos.

    Args:
        campos: Campos extraidos do contrato de honorarios.

    Returns:
        Texto do contrato preenchido. Campos ausentes aparecem como
        ``[A PREENCHER: <campo>]``. Nunca lanca excecao.
    """
    contratante = _placeholder(campos.contratante, "contratante")
    contratado = _placeholder(campos.contratado, "contratado")
    objeto = _placeholder(campos.objeto, "objeto")
    foro = _placeholder(campos.foro_eleicao, "foro_eleicao")
    forma = _FORMA_PAGAMENTO_TEXTO.get(
        campos.forma_pagamento, _FORMA_PAGAMENTO_TEXTO["desconhecido"]
    )

    if campos.valor is not None:
        valor_linha = (
            f"R$ {campos.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        valor_texto = f"o valor de {valor_linha}"
    else:
        valor_texto = "o valor de [A PREENCHER: valor]"

    if campos.percentual is not None:
        exito_linha = (
            f" Acrescido de honorarios de exito de {campos.percentual}% sobre o "
            "proveito economico obtido."
        )
    else:
        exito_linha = ""

    return (
        "CONTRATO DE PRESTACAO DE SERVICOS ADVOCATICIOS\n\n"
        f"CONTRATANTE: {contratante}.\n\n"
        f"CONTRATADO(A): {contratado}.\n\n"
        f"CLAUSULA 1a - DO OBJETO. {objeto}.\n\n"
        "CLAUSULA 2a - DOS HONORARIOS. A titulo de honorarios advocaticios, o(a) "
        f"contratante pagara ao(a) contratado(a) {valor_texto}. {forma}{exito_linha}\n\n"
        "CLAUSULA 3a - DO FORO. Fica eleito o foro da Comarca de "
        f"{foro} para dirimir quaisquer questoes oriundas deste contrato.\n\n"
        "______________________________\n"
        f"{contratante}\n\n"
        "______________________________\n"
        f"{contratado}\n"
    )
