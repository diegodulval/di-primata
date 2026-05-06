"""
Seed de desenvolvimento — Di Mata
Cria 3 tenants com usuários, unidades, protocolos, ciclos e lotes.
Requer a API rodando (make run).

    make seed
    # ou: .venv/bin/python scripts/seed.py
"""

import os
import sys
from uuid import uuid4

import httpx

BASE = os.getenv("API_URL", "http://localhost:8000")
SENHA = "dev1234"
_tokens: dict[str, str] = {}

# ── helpers ───────────────────────────────────────────────────────────────────


def ok(label: str, r: httpx.Response, expected: int = 200) -> dict:
    if r.status_code != expected:
        print(f"\n❌  {label} → HTTP {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    return r.json()


def bearer(email: str) -> dict:
    return {"Authorization": f"Bearer {_tokens[email]}"}


def register(c: httpx.Client, account: dict, admin: dict) -> str:
    data = ok("register", c.post("/auth/register", json={"account": account, "admin": admin}), 201)
    _tokens[admin["email"]] = data["access_token"]
    return data["access_token"]


def add_user(c: httpx.Client, token: str, user: dict, role: str = "OPERADOR") -> dict:
    r = c.post(f"/accounts/users?role={role}", json=user, headers={"Authorization": f"Bearer {token}"})
    u = ok("add_user", r, 201)
    # login para guardar token próprio
    lr = c.post("/auth/login", json={"email": user["email"], "senha": SENHA})
    if lr.status_code == 200:
        _tokens[user["email"]] = lr.json()["access_token"]
    return u


def create_unit(c: httpx.Client, token: str, body: dict) -> dict:
    return ok("create_unit", c.post("/units", json=body, headers={"Authorization": f"Bearer {token}"}), 201)


def create_protocol(c: httpx.Client, token: str, body: dict) -> dict:
    return ok("create_protocol", c.post("/units/protocols", json=body, headers={"Authorization": f"Bearer {token}"}), 201)


def create_cycle(c: httpx.Client, token: str, body: dict) -> dict:
    return ok("create_cycle", c.post("/cycles", json=body, headers={"Authorization": f"Bearer {token}"}), 201)


def transition(c: httpx.Client, token: str, cycle_id: str, status: str) -> dict:
    return ok(f"→{status}", c.patch(f"/cycles/{cycle_id}/status", json={"status": status}, headers={"Authorization": f"Bearer {token}"}))


def add_event(c: httpx.Client, token: str, cycle_id: str, body: dict) -> dict:
    return ok("add_event", c.post(f"/cycles/{cycle_id}/events", json=body, headers={"Authorization": f"Bearer {token}"}), 201)


def generate_lot(c: httpx.Client, token: str, cycle_id: str) -> dict:
    return ok("generate_lot", c.post(f"/cycles/{cycle_id}/lots", headers={"Authorization": f"Bearer {token}"}), 201)


def publish_lot(c: httpx.Client, token: str, lot_id: str) -> dict:
    return ok("publish_lot", c.post(f"/cycles/lots/{lot_id}/publish", headers={"Authorization": f"Bearer {token}"}))


def step(nome: str, tipo: str) -> dict:
    """Cria um step com ID pré-definido para referenciar em etapas_obrig_ids."""
    return {"id": str(uuid4()), "nome": nome, "tipo": tipo, "obrigatorio": True}


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    print("Di Mata — seed de desenvolvimento\n")

    with httpx.Client(base_url=BASE, timeout=15) as c:
        try:
            c.get("/health").raise_for_status()
        except Exception:
            print(f"❌  API indisponível em {BASE}\n    Execute: make run")
            sys.exit(1)

        published_lots: list[dict] = []

        # ── Tenant 1: Fazenda Vale do Café ────────────────────────────────────
        print("🌿  Tenant 1 — Fazenda Vale do Café (PREMIUM_AGRO / CAF)")

        tk1 = register(c,
            account={"nome": "Fazenda Vale do Café", "documento": "12.345.678/0001-90",
                     "email": "conta@cafe.dev", "plano": "PREMIUM_AGRO", "setor_primario": "CAF"},
            admin={"nome": "Marcelo Duarte", "email": "admin@cafe.dev",
                   "tipo": "PRODUTOR_RURAL", "senha": SENHA},
        )
        add_user(c, tk1, {"nome": "Sandra Lima", "email": "gerente@cafe.dev",
                          "tipo": "CONSULTOR_TECNICO", "senha": SENHA}, role="ADMIN")
        add_user(c, tk1, {"nome": "João Campos", "email": "operador@cafe.dev",
                          "tipo": "OPERADOR", "senha": SENHA}, role="OPERADOR")

        unit1 = create_unit(c, tk1, {"nome": "Talhão Norte", "tipo": "TALHAO",
                                      "setor_template": "CAF", "area_capacidade": 12.5,
                                      "lat": -21.7654, "lng": -46.5678})

        # steps com IDs pré-gerados no cliente
        s_colheita      = step("Colheita Seletiva",       "COLHEITA")
        s_secagem       = step("Secagem Natural",          "OPERACAO")
        s_beneficiamento = step("Beneficiamento",          "OPERACAO")
        s_qc            = step("Controle de Qualidade",    "CTRL_QUALIDADE")

        all_steps = [s_colheita, s_secagem, s_beneficiamento, s_qc]

        p1 = create_protocol(c, tk1, {
            "setor_template": "CAF", "nome": "Protocolo Café Especial v1", "versao": "1.0.0",
            "ref_normativa": "IN MAPA nº 51/2018",
            "etapas": all_steps,
            "etapas_obrig_ids": [s["id"] for s in all_steps],
        })

        # Ciclo 1 — fluxo completo → lote publicado
        print("    ↳ ciclo 1: Café Arábica Safra 2026 → lote publicado")
        cy1 = create_cycle(c, tk1, {"unit_id": unit1["id"], "protocol_id": p1["id"],
                                     "produto": "Café Arábica Especial",
                                     "meta_json": {"safra": "2026", "variedade": "Bourbon Amarelo"}})
        transition(c, tk1, cy1["id"], "EM_PRODUCAO")

        # todos os eventos ANTES de encerrar
        add_event(c, tk1, cy1["id"], {"etapa_protocolo_id": s_colheita["id"],
            "tipo_evento": "COLHEITA", "origem": "MANUAL",
            "descricao": "Colheita seletiva dos grãos cereja. Brix médio 22°.",
            "payload_json": {"brix": 22, "metodo": "seletiva", "volume_kg": 1800}})
        add_event(c, tk1, cy1["id"], {"etapa_protocolo_id": s_secagem["id"],
            "tipo_evento": "OPERACAO", "origem": "MANUAL",
            "descricao": "Secagem natural em terreiro suspenso. 18 dias.",
            "payload_json": {"dias": 18, "umidade_inicial_pct": 55}})
        add_event(c, tk1, cy1["id"], {"etapa_protocolo_id": s_beneficiamento["id"],
            "tipo_evento": "OPERACAO", "origem": "MANUAL",
            "descricao": "Beneficiamento a seco. Rendimento 78%.",
            "payload_json": {"rendimento_pct": 78, "sacas": 15}})
        add_event(c, tk1, cy1["id"], {"etapa_protocolo_id": s_qc["id"],
            "tipo_evento": "CTRL_QUALIDADE", "origem": "MANUAL",
            "descricao": "Catação manual. Score SCA: 86 pontos. Zero defeitos.",
            "payload_json": {"score_sca": 86, "defeitos": 0, "catacao": "manual"}})

        transition(c, tk1, cy1["id"], "ENCERRADO")
        transition(c, tk1, cy1["id"], "VALIDANDO")
        lot1 = generate_lot(c, tk1, cy1["id"])
        lot1 = publish_lot(c, tk1, lot1["id"])
        published_lots.append({"tenant": "Fazenda Vale do Café",
                                "produto": "Café Arábica Especial — Safra 2026",
                                "qr_hash": lot1["qr_hash"]})

        # Ciclo 2 — em andamento
        print("    ↳ ciclo 2: Café Robusta Safra 2026 → em produção")
        cy2 = create_cycle(c, tk1, {"unit_id": unit1["id"], "protocol_id": p1["id"],
                                     "produto": "Café Robusta", "meta_json": {"safra": "2026"}})
        transition(c, tk1, cy2["id"], "EM_PRODUCAO")

        # ── Tenant 2: Cooperativa Cacau Sul ───────────────────────────────────
        print("🍫  Tenant 2 — Cooperativa Cacau Sul (COOPERATIVA / CAC)")

        tk2 = register(c,
            account={"nome": "Cooperativa Cacau Sul", "documento": "98.765.432/0001-11",
                     "email": "conta@cacau.dev", "plano": "COOPERATIVA", "setor_primario": "CAC"},
            admin={"nome": "Beatriz Moraes", "email": "admin@cacau.dev",
                   "tipo": "PRODUTOR_RURAL", "senha": SENHA},
        )
        add_user(c, tk2, {"nome": "Rafael Nunes", "email": "operador@cacau.dev",
                          "tipo": "OPERADOR", "senha": SENHA}, role="OPERADOR")

        unit2 = create_unit(c, tk2, {"nome": "Linha de Processamento 1", "tipo": "LINHA_PRODUCAO",
                                      "setor_template": "CAC", "area_capacidade": 500.0})

        s_ferm = step("Fermentação",                "OPERACAO")
        s_sec  = step("Secagem ao Sol",             "OPERACAO")
        s_cls  = step("Classificação Granulométrica","CTRL_QUALIDADE")

        p2 = create_protocol(c, tk2, {
            "setor_template": "CAC", "nome": "Protocolo Cacau Fino v1", "versao": "1.0.0",
            "ref_normativa": "Decreto 7.623/2011",
            "etapas": [s_ferm, s_sec, s_cls],
            "etapas_obrig_ids": [s_ferm["id"], s_sec["id"], s_cls["id"]],
        })

        print("    ↳ ciclo: Cacau Fino de Aroma 2026 → em produção (1 evento)")
        cy3 = create_cycle(c, tk2, {"unit_id": unit2["id"], "protocol_id": p2["id"],
                                     "produto": "Cacau Fino de Aroma",
                                     "meta_json": {"safra": "2026", "origem": "Vale do Juliana-BA"}})
        transition(c, tk2, cy3["id"], "EM_PRODUCAO")
        add_event(c, tk2, cy3["id"], {"etapa_protocolo_id": s_ferm["id"],
            "tipo_evento": "OPERACAO", "origem": "MANUAL",
            "descricao": "Fermentação em caixas de madeira. 120h. pH final: 4.2.",
            "payload_json": {"horas": 120, "ph_final": 4.2, "temperatura_max_c": 48}})

        # ── Tenant 3: Artesanato Tear Vivo ────────────────────────────────────
        print("🧶  Tenant 3 — Artesanato Tear Vivo (CORE_PLUS / ART)")

        tk3 = register(c,
            account={"nome": "Artesanato Tear Vivo", "documento": "11.222.333/0001-44",
                     "email": "conta@tear.dev", "plano": "CORE_PLUS", "setor_primario": "ART"},
            admin={"nome": "Cláudia Mendes", "email": "admin@tear.dev",
                   "tipo": "ARTESAO", "senha": SENHA},
        )
        create_unit(c, tk3, {"nome": "Tear Principal", "tipo": "TEAR", "setor_template": "ART"})
        create_protocol(c, tk3, {
            "setor_template": "ART", "nome": "Protocolo Tear Manual v1", "versao": "1.0.0",
            "etapas": [step("Tingimento Natural", "OPERACAO"), step("Tecelagem", "OPERACAO")],
            "etapas_obrig_ids": [],
        })
        print("    ↳ sem ciclos — estado vazio para testes de UI")

        # ── Relatório ─────────────────────────────────────────────────────────
        SEP = "─" * 64
        print(f"\n{SEP}")
        print("SEED CONCLUÍDO\n")

        USERS = [
            ("Fazenda Vale do Café",  "admin@cafe.dev",     "ADMIN",    SENHA),
            ("Fazenda Vale do Café",  "gerente@cafe.dev",   "ADMIN",    SENHA),
            ("Fazenda Vale do Café",  "operador@cafe.dev",  "OPERADOR", SENHA),
            ("Cooperativa Cacau Sul", "admin@cacau.dev",    "ADMIN",    SENHA),
            ("Cooperativa Cacau Sul", "operador@cacau.dev", "OPERADOR", SENHA),
            ("Artesanato Tear Vivo",  "admin@tear.dev",     "ADMIN",    SENHA),
        ]
        print(f"  {'Tenant':<26} {'E-mail':<28} {'Role':<10} Senha")
        print(f"  {SEP}")
        for tenant, email, role, senha in USERS:
            print(f"  {tenant:<26} {email:<28} {role:<10} {senha}")

        print("\n  Portal QR público (consumidor — sem login):")
        for lot in published_lots:
            print(f"  └─ {lot['produto']}")
            print(f"     http://localhost:5174/p/{lot['qr_hash']}")

        print(f"\n  Dashboard → http://localhost:5173")
        print(f"  API docs  → http://localhost:8000/docs")
        print(SEP)


if __name__ == "__main__":
    main()
