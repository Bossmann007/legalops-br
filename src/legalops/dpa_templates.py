"""DPA Templates — Acordo de Tratamento de Dados / Operador (Art. 39 LGPD).

Renderiza um Acordo de Tratamento de Dados (Data Processing Agreement) em pt-BR
com as clausulas padrao da LGPD para a relacao controlador-operador.

Deterministico, stdlib only. ``render_dpa`` nunca levanta excecao: campos
ausentes viram placeholder ``[A PREENCHER: <campo>]``.

Uso:
    >>> from legalops.dpa_templates import DPAParams, render_dpa
    >>> p = DPAParams(
    ...     controlador="Escritorio X",
    ...     operador="Fornecedor Y",
    ...     objeto="hospedagem de dados",
    ...     finalidade="prestacao de servico SaaS",
    ...     categorias_dados=("nome", "email"),
    ...     prazo_retencao="vigencia do contrato",
    ...     suboperadores_permitidos=False,
    ...     transferencia_internacional=False,
    ... )
    >>> "ACORDO DE TRATAMENTO DE DADOS" in render_dpa(p)
    True
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "DPAParams",
    "clausulas_obrigatorias",
    "render_dpa",
]


@dataclass(frozen=True)
class DPAParams:
    """Parametros para renderizar um DPA (Art. 39).

    Attributes:
        controlador: Nome do controlador de dados.
        operador: Nome do operador de dados.
        objeto: Objeto do acordo.
        finalidade: Finalidade do tratamento.
        categorias_dados: Categorias de dados tratados.
        prazo_retencao: Prazo de retencao acordado.
        suboperadores_permitidos: Se a subcontratacao e permitida.
        transferencia_internacional: Se ha transferencia internacional (Art. 33).
    """

    controlador: str
    operador: str
    objeto: str
    finalidade: str
    categorias_dados: tuple[str, ...]
    prazo_retencao: str
    suboperadores_permitidos: bool
    transferencia_internacional: bool


def clausulas_obrigatorias() -> tuple[str, ...]:
    """Retorna os titulos das clausulas obrigatorias do DPA (checklist)."""
    return (
        "1. DO OBJETO",
        "2. DAS DEFINICOES",
        "3. DAS OBRIGACOES DO OPERADOR (Art. 39)",
        "4. DA SEGURANCA DA INFORMACAO (Art. 46-49)",
        "5. DA SUBCONTRATACAO",
        "6. DA TRANSFERENCIA INTERNACIONAL (Art. 33)",
        "7. DO TERMINO E DEVOLUCAO/ELIMINACAO",
        "8. DA RESPONSABILIDADE",
    )


def _campo(valor: str, nome: str) -> str:
    """Retorna o valor ou um placeholder se vazio."""
    return valor if valor and valor.strip() else f"[A PREENCHER: {nome}]"


def _categorias(cats: tuple[str, ...]) -> str:
    validas = [c for c in cats if c and c.strip()]
    if not validas:
        return "[A PREENCHER: categorias_dados]"
    return ", ".join(validas)


def render_dpa(params: DPAParams) -> str:
    """Renderiza um Acordo de Tratamento de Dados (Operador) em pt-BR.

    Args:
        params: Parametros do acordo.

    Returns:
        Texto completo do DPA com clausulas padrao da LGPD. Campos ausentes
        sao substituidos por ``[A PREENCHER: <campo>]``. Nunca levanta excecao.
    """
    controlador = _campo(params.controlador, "controlador")
    operador = _campo(params.operador, "operador")
    objeto = _campo(params.objeto, "objeto")
    finalidade = _campo(params.finalidade, "finalidade")
    categorias = _categorias(params.categorias_dados)
    prazo = _campo(params.prazo_retencao, "prazo_retencao")

    if params.suboperadores_permitidos:
        clausula_sub = (
            "5. DA SUBCONTRATACAO\n"
            "O OPERADOR podera subcontratar suboperadores, mediante autorizacao "
            "previa e por escrito do CONTROLADOR, impondo aos suboperadores as "
            "mesmas obrigacoes de protecao de dados aqui previstas."
        )
    else:
        clausula_sub = (
            "5. DA SUBCONTRATACAO\n"
            "E vedada ao OPERADOR a subcontratacao de suboperadores sem "
            "autorizacao previa e expressa do CONTROLADOR."
        )

    if params.transferencia_internacional:
        clausula_transf = (
            "6. DA TRANSFERENCIA INTERNACIONAL (Art. 33)\n"
            "Eventual transferencia internacional de dados observara as "
            "hipoteses do Art. 33 da LGPD, com garantias adequadas de protecao "
            "e ciencia previa do CONTROLADOR."
        )
    else:
        clausula_transf = (
            "6. DA TRANSFERENCIA INTERNACIONAL (Art. 33)\n"
            "O OPERADOR nao realizara transferencia internacional dos dados sem "
            "autorizacao previa e expressa do CONTROLADOR, observado o Art. 33."
        )

    return f"""ACORDO DE TRATAMENTO DE DADOS (OPERADOR)

Celebrado entre {controlador} ("CONTROLADOR") e {operador} ("OPERADOR"), nos
termos da Lei 13.709/2018 (LGPD).

1. DO OBJETO
O presente acordo tem por objeto {objeto}, regulando o tratamento de dados
pessoais realizado pelo OPERADOR por conta e ordem do CONTROLADOR.

2. DAS DEFINICOES
Os termos "dado pessoal", "tratamento", "controlador" e "operador" possuem o
significado atribuido pelo Art. 5 da LGPD.
Finalidade do tratamento: {finalidade}.
Categorias de dados tratados: {categorias}.

3. DAS OBRIGACOES DO OPERADOR (Art. 39)
O OPERADOR obriga-se a tratar os dados pessoais estritamente conforme as
instrucoes documentadas do CONTROLADOR e para a finalidade aqui definida,
abstendo-se de qualquer tratamento diverso.

4. DA SEGURANCA DA INFORMACAO (Art. 46-49)
O OPERADOR adotara medidas de seguranca tecnicas e administrativas aptas a
proteger os dados pessoais de acessos nao autorizados e de situacoes acidentais
ou ilicitas, comunicando ao CONTROLADOR qualquer incidente de seguranca.

{clausula_sub}

{clausula_transf}

7. DO TERMINO E DEVOLUCAO/ELIMINACAO
Encerrado o tratamento, e observado o prazo de retencao ({prazo}), o OPERADOR
devolvera ou eliminara os dados pessoais e suas copias, salvo obrigacao legal
de conservacao.

8. DA RESPONSABILIDADE
O OPERADOR responde solidariamente pelos danos causados em razao de tratamento
em desconformidade com a LGPD ou com as instrucoes licitas do CONTROLADOR,
nos termos do Art. 42.
"""
