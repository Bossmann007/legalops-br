"""Gerador de corpus sintetico para validar pii-redactor-br.

Uso:
    python corpus/synthetic/generate.py --count 100 --out corpus/synthetic/docs/

Output: arquivos JSON com texto sintetico + count esperado de PII.
NUNCA usa dados reais — Faker pt-BR + templates juridicos.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import uuid
from pathlib import Path

from faker import Faker

# (template, expected_count, expected_by_type, tribunal)
TEMPLATES: list[tuple[str, int, dict[str, int], str]] = [
    (
        "Procurador OAB/{uf} {oab_n}, em nome do cliente CPF {cpf}, "
        "comunica que a empresa CNPJ {cnpj} efetuou pagamento via PIX para "
        "{email}. Telefone de contato: {phone}.",
        5,
        {"OAB": 1, "CPF": 1, "CNPJ": 1, "EMAIL": 1, "PHONE_BR": 1},
        "neutro",
    ),
    (
        "Acao trabalhista. Reclamante CPF {cpf}. Reclamada CNPJ {cnpj}. "
        "Procuradora OAB-{uf} {oab_n}. Email: {email}.",
        4,
        {"CPF": 1, "CNPJ": 1, "OAB": 1, "EMAIL": 1},
        "neutro",
    ),
    (
        "Contrato de prestacao de servicos entre {cnpj} e cliente CPF {cpf}. "
        "Pagamento via PIX chave {pix_uuid}. Comunicacoes para {email}.",
        4,
        {"CNPJ": 1, "CPF": 1, "PIX_UUID": 1, "EMAIL": 1},
        "neutro",
    ),
    (
        "Processo movido por procurador OAB/{uf} {oab_n}. Cliente: CPF {cpf}.",
        2,
        {"OAB": 1, "CPF": 1},
        "neutro",
    ),
    (
        "Documento sem dados pessoais — apenas texto comum sobre direito processual.",
        0,
        {},
        "neutro",
    ),
    # TJPR / Projudi
    (
        "Sistema Projudi - Tribunal de Justica do Parana\n"
        "Processo: {cnj_pr}\n"
        "Vara: 2a Vara Civel - Comarca de Curitiba\n"
        "Despacho: Intime-se o procurador OAB/PR {oab_n}, "
        "patrono do cliente CPF {cpf}, no prazo de 15 dias uteis. "
        "Publicado em {data}. Email cadastrado: {email}.",
        3,
        {"OAB": 1, "CPF": 1, "EMAIL": 1},
        "tjpr",
    ),
    (
        "Projudi - Encaminhamento de intimacao\n"
        "Autos {cnj_pr}\n"
        "Vara Trabalhista de Londrina. Sentenca prolatada em {data}. "
        "Prazo de 8 dias para recurso. Reclamante CPF {cpf}. "
        "Reclamada CNPJ {cnpj}.",
        2,
        {"CPF": 1, "CNPJ": 1},
        "tjpr",
    ),
    # TJSP / e-SAJ
    (
        "Tribunal de Justica de Sao Paulo - e-SAJ\n"
        "Autos nro {cnj_sp}\n"
        "3a Vara Civel - Foro Regional de Santo Amaro\n"
        "Decisao: Intime-se a parte autora para manifestacao em prazo peremptorio "
        "de 10 dias. Publicado em {data}. Procurador OAB/SP {oab_n}. "
        "CPF do autor: {cpf}.",
        2,
        {"OAB": 1, "CPF": 1},
        "tjsp",
    ),
    (
        "PJe-SP - Notificacao automatica\n"
        "Processo nro {cnj_sp}\n"
        "1a Vara da Familia - Comarca de Campinas\n"
        "Sentenca de procedencia parcial. Prazo de 15 dias para apelacao. "
        "Data: {data}. Email do procurador: {email}.",
        1,
        {"EMAIL": 1},
        "tjsp",
    ),
    (
        "e-SAJ - Tribunal de Justica de Sao Paulo\n"
        "Autos: {cnj_sp}\n"
        "Vara Empresarial - Foro Central\n"
        "Despacho: cumpra-se. Empresa CNPJ {cnpj}. Publicado em {data}. "
        "PIX chave para custas: {pix_uuid}.",
        2,
        {"CNPJ": 1, "PIX_UUID": 1},
        "tjsp",
    ),
]


def gen_cpf() -> str:
    n = [random.randint(0, 9) for _ in range(9)]
    return f"{n[0]}{n[1]}{n[2]}.{n[3]}{n[4]}{n[5]}.{n[6]}{n[7]}{n[8]}-{random.randint(10, 99)}"


def gen_cnpj() -> str:
    n = [random.randint(0, 9) for _ in range(8)]
    return f"{n[0]}{n[1]}.{n[2]}{n[3]}{n[4]}.{n[5]}{n[6]}{n[7]}/0001-{random.randint(10, 99)}"


def gen_cnj(tribunal_code: str) -> str:
    """CNJ format NNNNNNN-DD.AAAA.J.TR.OOOO. tribunal_code: 8.16=TJPR, 8.26=TJSP."""
    n = random.randint(1000000, 9999999)
    dv = random.randint(10, 99)
    ano = random.choice([2024, 2025, 2026])
    orgao = random.randint(1, 9999)
    return f"{n:07d}-{dv:02d}.{ano}.{tribunal_code}.{orgao:04d}"


def gen_data() -> str:
    """DDMMYYYY string for templates."""
    day = random.randint(1, 28)
    month = random.randint(1, 12)
    year = random.choice([2025, 2026])
    return f"{day:02d}/{month:02d}/{year}"


def gen_doc(fake: Faker, idx: int) -> dict[str, object]:
    template, expected, expected_by_type, tribunal = random.choice(TEMPLATES)
    text = template.format(
        cpf=gen_cpf(),
        cnpj=gen_cnpj(),
        uf=random.choice(["PR", "SP", "RJ", "MG", "RS"]),
        oab_n=random.randint(1000, 99999),
        email=f"{fake.user_name()}@test.local",
        phone=f"+55 41 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
        pix_uuid=str(uuid.uuid4()),
        cnj_pr=gen_cnj("8.16"),
        cnj_sp=gen_cnj("8.26"),
        data=gen_data(),
    )
    return {
        "id": f"synthetic-{idx:04d}",
        "text": text,
        "expected_pii_count": expected,
        "expected_by_type": expected_by_type,
        "tribunal": tribunal,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, default=Path("corpus/synthetic/docs"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    fake = Faker("pt_BR")
    Faker.seed(args.seed)

    args.out.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        doc = gen_doc(fake, i)
        out = args.out / f"doc_{i:04d}.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated {args.count} synthetic docs in {args.out}")


if __name__ == "__main__":
    main()
