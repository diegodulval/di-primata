"""
Seed de desenvolvimento — Di Auto 
Valida o admin criado pelo SQL (004_seed.sql) e popula dados de exemplo:
  - 2 clientes
  - 2 veículos vinculados
  - 3 produtos em estoque
  - 1 fornecedor

Requer:
  - API rodando em :8001 (make run-oficinas)
  - Migrations aplicadas (make migrate-oficinas)

    make seed-oficinas
    # ou: uv run --package oficinas python scripts/seed_oficinas.py
"""

import os
import sys

import httpx

BASE = os.getenv("OFICINAS_API_URL", "http://localhost:8001")
ADMIN_EMAIL = "admin@oficina.dev"
ADMIN_SENHA = "dev1234"
_token: str = ""


# ── helpers ───────────────────────────────────────────────────────────────────


def ok(label: str, r: httpx.Response, expected: int = 200) -> dict:
    if r.status_code != expected:
        print(f"\n❌  {label} → HTTP {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    data = r.json()
    return data


def auth() -> dict:
    return {"Authorization": f"Bearer {_token}"}


def post(c: httpx.Client, path: str, body: dict, expected: int = 201) -> dict:
    return ok(path, c.post(path, json=body, headers=auth()), expected)


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    global _token

    print("Di Auto — seed de desenvolvimento\n")

    with httpx.Client(base_url=BASE, timeout=15) as c:
        # Verifica saúde da API
        try:
            c.get("/health").raise_for_status()
        except Exception:
            print(f"❌  API indisponível em {BASE}")
            print("    Execute: make run-oficinas")
            sys.exit(1)

        # Login com o admin criado pelo SQL seed
        print(f"🔑  Login como {ADMIN_EMAIL} ...", end=" ")
        r = c.post("/auth/login", json={"identificador": ADMIN_EMAIL, "senha": ADMIN_SENHA})
        if r.status_code != 200:
            print(f"FALHOU (HTTP {r.status_code})")
            print("    Verifique se as migrations foram aplicadas: make migrate-oficinas")
            sys.exit(1)
        _token = r.json()["access_token"]
        perfil = r.json()["perfil"]
        print(f"OK  (perfil={perfil})")

        # Perfil do usuário logado
        me = ok("GET /usuarios/me", c.get("/usuarios/me", headers=auth()))
        tenant_id = me["tenant_id"]

        # ── Veículos ──────────────────────────────────────────────────────────
        print("\n🚗  Veículos ...")

        v1 = post(c, "/veiculos", {
            "placa": "ABC1234",
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano_fab": 2019,
            "ano_mod": 2020,
            "cor": "Prata",
            "tipo": "carro",
        })
        print(f"    ✓ {v1['placa']} — {v1.get('marca')} {v1.get('modelo')}")

        v2 = post(c, "/veiculos", {
            "placa": "XYZ9J87",
            "marca": "Honda",
            "modelo": "CG 160",
            "ano_fab": 2022,
            "ano_mod": 2022,
            "cor": "Vermelha",
            "tipo": "moto",
        })
        print(f"    ✓ {v2['placa']} — {v2.get('marca')} {v2.get('modelo')}")

        # ── Clientes ──────────────────────────────────────────────────────────
        print("\n👤  Clientes ...")

        c1 = post(c, "/clientes", {
            "nome": "João da Silva",
            "cpf_cnpj": "12345678901",
            "telefone": "+5511987654321",
            "email": "joao@email.com",
        })
        print(f"    ✓ {c1['nome']}  (id={c1['id'][:8]}…)")

        c2 = post(c, "/clientes", {
            "nome": "Auto Peças Rápida LTDA",
            "cpf_cnpj": "11222333000144",
            "telefone": "+5511333334444",
        })
        print(f"    ✓ {c2['nome']}  (id={c2['id'][:8]}…)")

        # Vincula veículos aos clientes
        post(c, f"/clientes/{c1['id']}/veiculos", {"veiculo_id": v1["id"]})
        print(f"    ✓ {v1['placa']} vinculado a {c1['nome']}")

        post(c, f"/clientes/{c2['id']}/veiculos", {"veiculo_id": v2["id"]})
        print(f"    ✓ {v2['placa']} vinculado a {c2['nome']}")

        # ── Produtos ──────────────────────────────────────────────────────────
        print("\n📦  Produtos em estoque ...")

        produtos = [
            {
                "codigo": "FLT001",
                "descricao": "FILTRO DE OLEO MANN W712/75",
                "ncm": "84212300",
                "marca": "MANN",
                "preco_custo": "18.50",
                "preco_venda": "35.00",
                "estoque_minimo": "5",
            },
            {
                "codigo": "VLA001",
                "descricao": "VELA DE IGNICAO NGK BKR5E",
                "ncm": "85111000",
                "marca": "NGK",
                "preco_custo": "12.00",
                "preco_venda": "22.00",
                "estoque_minimo": "10",
            },
            {
                "codigo": "OLM001",
                "descricao": "OLEO MOTOR CASTROL GTX 5W30 1L",
                "ncm": "27101999",
                "marca": "CASTROL",
                "preco_custo": "28.00",
                "preco_venda": "45.00",
                "estoque_minimo": "6",
            },
        ]

        for p in produtos:
            prod = post(c, "/produtos", p)
            print(f"    ✓ [{prod['codigo']}] {prod['descricao']}")

        # ── Relatório ─────────────────────────────────────────────────────────
        SEP = "─" * 60
        print(f"\n{SEP}")
        print("SEED CONCLUÍDO\n")
        print(f"  Tenant ID : {tenant_id}")
        print()
        print(f"  {'E-mail / WhatsApp':<30} {'Perfil':<12} Senha")
        print(f"  {'-' * 58}")
        print(f"  {'admin@oficina.dev':<30} {'ADMIN':<12} {ADMIN_SENHA}")
        print()
        print("  Dados de exemplo:")
        print(f"  ├─ Clientes: {c1['nome']}, {c2['nome']}")
        print(f"  ├─ Veículos: {v1['placa']}, {v2['placa']}")
        print(f"  └─ Produtos: FLT001, VLA001, OLM001")
        print()
        print(f"  API docs → {BASE}/docs")
        print(f"  Frontend → http://localhost:5175")
        print(SEP)


if __name__ == "__main__":
    main()
