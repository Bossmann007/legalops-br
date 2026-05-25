"""Profile estruturado do escritorio Maffini Advocacia.

Gerado por cold-start interview com Tia May. Sem PII real — apenas placeholders.
Usado por agentes Claude Projects pra ter contexto sem ingerir vault inteiro.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AreaPratica(StrEnum):
    BANCARIO = "bancario"
    CONSUMIDOR = "consumidor"
    CIVEL = "civel"
    EMPRESARIAL = "empresarial"
    DIGITAL = "digital"
    LGPD = "lgpd"
    M_E_A = "m_e_a"
    TRABALHISTA = "trabalhista"


@dataclass(frozen=True)
class TeseRecorrente:
    """Tese juridica que o escritorio usa com frequencia."""

    titulo: str
    area: AreaPratica
    fundamentos: tuple[str, ...]
    notas: str = ""


@dataclass(frozen=True)
class PracticeProfile:
    """Profile estruturado do escritorio Maffini."""

    escritorio: str = "Maffini Advocacia"
    advogada_responsavel: str = "[OAB_REDACTED]"
    cidade: str = "Curitiba"
    estado: str = "PR"
    areas_atuacao: tuple[AreaPratica, ...] = ()
    tribunais_principais: tuple[str, ...] = ()
    teses_recorrentes: tuple[TeseRecorrente, ...] = ()
    politica_honorarios: str = ""
    politica_ia: str = ""


DEFAULT_PROFILE = PracticeProfile(
    areas_atuacao=(
        AreaPratica.BANCARIO,
        AreaPratica.CONSUMIDOR,
        AreaPratica.CIVEL,
        AreaPratica.EMPRESARIAL,
        AreaPratica.LGPD,
    ),
    tribunais_principais=("TJPR", "TRF4", "STJ", "STF"),
    teses_recorrentes=(
        TeseRecorrente(
            titulo="Revisao de contrato bancario com juros abusivos",
            area=AreaPratica.BANCARIO,
            fundamentos=("CDC art. 51 IV", "CC art. 421", "Sumula 297 STJ"),
        ),
        TeseRecorrente(
            titulo="Capitalizacao mensal de juros (anatocismo)",
            area=AreaPratica.BANCARIO,
            fundamentos=("Sumula 539 STJ", "MP 1.963-17/2000"),
        ),
        TeseRecorrente(
            titulo="Dano moral por inscricao indevida em cadastro de inadimplentes",
            area=AreaPratica.CONSUMIDOR,
            fundamentos=("CDC art. 14", "Sumula 385 STJ", "CDC art. 43"),
        ),
        TeseRecorrente(
            titulo="LGPD - vazamento de dados pessoais e responsabilidade civil",
            area=AreaPratica.LGPD,
            fundamentos=("LGPD art. 44", "LGPD art. 42", "CDC art. 14"),
        ),
    ),
    politica_honorarios="Faixa por tipo de causa, com proposta personalizada apos triagem.",
    politica_ia=(
        "Uso assistido com aprovacao item-a-item. Nenhuma decisao final automatizada. "
        "Gate LGPD obrigatorio antes de envio a LLMs externas. "
        "Logs auditaveis via oab_sigilo."
    ),
)


def get_teses_by_area(
    profile: PracticeProfile, area: AreaPratica
) -> tuple[TeseRecorrente, ...]:
    """Retorna teses filtradas por area."""
    return tuple(t for t in profile.teses_recorrentes if t.area == area)


def profile_summary(profile: PracticeProfile) -> str:
    """Gera resumo markdown do profile (sem PII). Util pra anexar a Claude Projects."""
    areas = ", ".join(a.value for a in profile.areas_atuacao)
    tribunais = ", ".join(profile.tribunais_principais)

    teses_md = "\n".join(
        f"- **{t.titulo}** ({t.area.value}): {', '.join(t.fundamentos)}"
        for t in profile.teses_recorrentes
    )

    return (
        f"# Profile {profile.escritorio}\n\n"
        f"- Cidade/UF: {profile.cidade}/{profile.estado}\n"
        f"- Advogada responsavel: {profile.advogada_responsavel}\n"
        f"- Areas: {areas}\n"
        f"- Tribunais principais: {tribunais}\n\n"
        f"## Teses Recorrentes\n\n{teses_md}\n\n"
        f"## Politica de Honorarios\n\n{profile.politica_honorarios}\n\n"
        f"## Politica IA\n\n{profile.politica_ia}\n"
    )
