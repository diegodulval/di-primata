"""
Testes de integração via HTTP — cobre o fluxo completo do sistema.
Cada teste recebe um `client` com store isolado (sem estado compartilhado).
"""
from uuid import uuid4


# ── auth ──────────────────────────────────────────────────────────────────────

def test_register_e_login(client):
    payload = {
        "account": {
            "nome": "Fazenda Auth",
            "documento": "11.111.111/0001-11",
            "email": "conta@auth.io",
            "plano": "FREE",
            "setor_primario": "CAF",
        },
        "admin": {
            "nome": "Admin",
            "email": "admin@auth.io",
            "tipo": "PRODUTOR_RURAL",
            "senha": "abc123",
        },
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201
    assert "access_token" in r.json()

    r = client.post("/auth/login", json={"email": "admin@auth.io", "senha": "abc123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_endpoint_protegido_sem_token_retorna_403(client):
    r = client.get("/accounts/me")
    assert r.status_code in (401, 403)


def test_endpoint_protegido_com_token_retorna_200(client, auth_headers):
    r = client.get("/accounts/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "conta@http.io"


# ── unidade + protocolo ───────────────────────────────────────────────────────

def test_criar_unidade(client, auth_headers):
    r = client.post(
        "/units",
        json={"nome": "Talhão A", "tipo": "TALHAO", "setor_template": "CAF"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["nome"] == "Talhão A"


def test_criar_protocolo(client, auth_headers):
    step_id = str(uuid4())
    r = client.post(
        "/units/protocols",
        json={
            "setor_template": "CAF",
            "nome": "Protocolo Test",
            "versao": "1.0.0",
            "etapas": [{"id": step_id, "nome": "Colheita", "tipo": "COLHEITA"}],
            "etapas_obrig_ids": [step_id],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["versao"] == "1.0.0"


# ── golden path: register → QR scan ──────────────────────────────────────────

def test_golden_path_completo(client, auth_headers):
    # 1. Criar unidade
    unit = client.post(
        "/units",
        json={"nome": "VGH", "tipo": "TALHAO", "setor_template": "CAF"},
        headers=auth_headers,
    ).json()

    # 2. Criar protocolo com 1 etapa obrigatória
    step_id = str(uuid4())
    protocol = client.post(
        "/units/protocols",
        json={
            "setor_template": "CAF",
            "nome": "P. Café",
            "versao": "1.0",
            "etapas": [{"id": step_id, "nome": "Colheita", "tipo": "COLHEITA"}],
            "etapas_obrig_ids": [step_id],
        },
        headers=auth_headers,
    ).json()

    # 3. Abrir ciclo
    cycle = client.post(
        "/cycles",
        json={"unit_id": unit["id"], "protocol_id": protocol["id"], "produto": "Café Especial"},
        headers=auth_headers,
    ).json()
    assert cycle["status"] == "ABERTO"

    # 4. Registrar evento cobrindo a etapa obrigatória
    client.post(
        f"/cycles/{cycle['id']}/events",
        json={
            "etapa_protocolo_id": step_id,
            "tipo_evento": "COLHEITA",
            "descricao": "Colheita do lote A",
            "origem": "MANUAL",
        },
        headers=auth_headers,
    )

    # 5. Avançar status: ABERTO → EM_PRODUCAO → ENCERRADO → VALIDANDO
    for status in ["EM_PRODUCAO", "ENCERRADO", "VALIDANDO"]:
        r = client.patch(
            f"/cycles/{cycle['id']}/status",
            json={"status": status},
            headers=auth_headers,
        )
        assert r.status_code == 200, f"Falhou em {status}: {r.text}"

    # 6. Gerar lote
    lot = client.post(
        f"/cycles/{cycle['id']}/lots",
        headers=auth_headers,
    ).json()
    assert lot["status"] == "GERADO"
    assert lot["codigo_lote"] == cycle["codigo"]
    assert len(lot["assets"]) == 1

    # 7. Publicar lote
    published = client.post(
        f"/cycles/lots/{lot['id']}/publish",
        headers=auth_headers,
    ).json()
    assert published["status"] == "PUBLICADO"
    assert published["publico"] is True

    # 8. Portal público — sem autenticação
    qr_hash = lot["qr_hash"]
    public = client.get(f"/p/{qr_hash}")
    assert public.status_code == 200
    data = public.json()
    assert data["produto"] == "Café Especial"
    assert data["codigo_lote"] == cycle["codigo"]


def test_gerar_lote_sem_cobrir_etapas_retorna_422(client, auth_headers):
    step_id = str(uuid4())
    unit = client.post(
        "/units",
        json={"nome": "U1", "tipo": "TALHAO", "setor_template": "CAF"},
        headers=auth_headers,
    ).json()
    protocol = client.post(
        "/units/protocols",
        json={
            "setor_template": "CAF",
            "nome": "P",
            "versao": "1.0",
            "etapas": [{"id": step_id, "nome": "Colheita", "tipo": "COLHEITA"}],
            "etapas_obrig_ids": [step_id],
        },
        headers=auth_headers,
    ).json()
    cycle = client.post(
        "/cycles",
        json={"unit_id": unit["id"], "protocol_id": protocol["id"], "produto": "X"},
        headers=auth_headers,
    ).json()

    for status in ["EM_PRODUCAO", "ENCERRADO", "VALIDANDO"]:
        client.patch(f"/cycles/{cycle['id']}/status", json={"status": status}, headers=auth_headers)

    r = client.post(f"/cycles/{cycle['id']}/lots", headers=auth_headers)
    assert r.status_code == 422


def test_portal_publico_lote_inexistente_retorna_404(client):
    r = client.get("/p/hash-que-nao-existe")
    assert r.status_code == 404
