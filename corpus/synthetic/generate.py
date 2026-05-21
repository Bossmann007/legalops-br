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

TEMPLATES = [
    (
        "Procurador OAB/{uf} {oab_n}, em nome do cliente CPF {cpf}, "
        "comunica que a empresa CNPJ {cnpj} efetuou pagamento via PIX para "
        "{email}. Telefone de contato: {phone}.",
        5,
    ),
    (
        "Acao trabalhista. Reclamante CPF {cpf}. Reclamada CNPJ {cnpj}. "
        "Procuradora OAB-{uf} {oab_n}. Email: {email}.",
        4,
    ),
    (
        "Contrato de prestacao de servicos entre {cnpj} e cliente CPF {cpf}. "
        "Pagamento via PIX chave {pix_uuid}. Comunicacoes para {email}.",
        4,
    ),
    (
        "Processo movido por procurador OAB/{uf} {oab_n}. Cliente: CPF {cpf}.",
        2,
    ),
    (
        "Documento sem dados pessoais — apenas texto comum sobre direito processual.",
        0,
    ),
]


def gen_cpf() -> str:
    n = [random.randint(0, 9) for _ in range(9)]
    return (
        f"{n[0]}{n[1]}{n[2]}.{n[3]}{n[4]}{n[5]}.{n[6]}{n[7]}{n[8]}-"
        f"{random.randint(10, 99)}"
    )


def gen_cnpj() -> str:
    n = [random.randint(0, 9) for _ in range(8)]
    return (
        f"{n[0]}{n[1]}.{n[2]}{n[3]}{n[4]}.{n[5]}{n[6]}{n[7]}/0001-"
        f"{random.randint(10, 99)}"
    )


def gen_doc(fake: Faker, idx: int) -> dict[str, object]:
    template, expected = random.choice(TEMPLATES)
    text = template.format(
        cpf=gen_cpf(),
        cnpj=gen_cnpj(),
        uf=random.choice(["PR", "SP", "RJ", "MG", "RS"]),
        oab_n=random.randint(1000, 99999),
        email=f"{fake.user_name()}@test.local",
        phone=f"+55 41 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
        pix_uuid=str(uuid.uuid4()),
    )
    return {
        "id": f"synthetic-{idx:04d}",
        "text": text,
        "expected_pii_count": expected,
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
