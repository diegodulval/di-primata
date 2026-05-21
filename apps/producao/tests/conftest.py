from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from auth.jwt import hash_password
from producao.main import app
from core.models.account import Account
from core.models.enums import (
    PlanoAssinatura,
    RolePerfil,
    TipoAgente,
    TipoUnidade,
)
from core.models.protocol import Protocol, ProtocolStep
from core.models.unit import Unit
from core.models.user import Profile, User
from producao.repositories.store import Store, get_store


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.fixture
def client(store: Store):
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded(store: Store) -> dict:
    """Store pré-populado com account + user + unit + protocol."""
    account = Account(
        nome="Fazenda Teste",
        documento="12.345.678/0001-90",
        email="conta@teste.io",
        plano=PlanoAssinatura.PREMIUM_AGRO,
        setor_primario="CAF",
    )
    store.accounts.save(account)

    user = User(
        account_id=account.id,
        nome="Admin",
        email="admin@teste.io",
        tipo=TipoAgente.PRODUTOR_RURAL,
        senha_hash=hash_password("senha123"),
    )
    store.users.save(user)

    profile = Profile(account_id=account.id, user_id=user.id, role=RolePerfil.ADMIN)
    store.profiles.save(profile)

    unit = Unit(
        account_id=account.id,
        nome="VGH",
        tipo=TipoUnidade.TALHAO,
        setor_template="CAF",
    )
    store.units.save(unit)

    step = ProtocolStep(nome="Colheita", tipo="COLHEITA", obrigatorio=True)
    protocol = Protocol(
        setor_template="CAF",
        nome="Protocolo Café v1",
        versao="1.0.0",
        etapas=[step],
        etapas_obrig_ids=[step.id],
    )
    store.protocols.save(protocol)

    return {
        "account": account,
        "user": user,
        "profile": profile,
        "unit": unit,
        "protocol": protocol,
        "step": step,
    }


# ── payload reutilizável para registro HTTP ────────────────────────────────────
REGISTER_PAYLOAD = {
    "account": {
        "nome": "Fazenda HTTP",
        "documento": "98.765.432/0001-10",
        "email": "conta@http.io",
        "plano": "FREE",
        "setor_primario": "CAF",
    },
    "admin": {
        "nome": "Admin HTTP",
        "email": "admin@http.io",
        "tipo": "PRODUTOR_RURAL",
        "senha": "senha123",
    },
}


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    resp = client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
