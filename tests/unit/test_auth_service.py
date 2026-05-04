import pytest
from fastapi import HTTPException

from app.models.account import AccountCreate
from app.models.enums import RolePerfil, TipoAgente
from app.models.user import UserCreate
from app.services.auth_service import AuthService

_ACCT = AccountCreate(nome="X", documento="000", email="conta@x.io", setor_primario="AGRO")
_ADMIN = UserCreate(nome="Admin", email="admin@x.io", tipo=TipoAgente.PRODUTOR_RURAL, senha="senha123")


def test_register_cria_account_user_profile(store):
    svc = AuthService(store)
    account, user, token = svc.register_account(_ACCT, _ADMIN)

    assert store.accounts.get(account.id) is not None
    assert store.users.get(user.id) is not None
    assert store.profiles.find_one(user_id=user.id) is not None
    assert isinstance(token, str) and len(token) > 10


def test_register_email_duplicado_levanta_400(store):
    svc = AuthService(store)
    svc.register_account(_ACCT, _ADMIN)
    with pytest.raises(HTTPException) as exc:
        svc.register_account(_ACCT, _ADMIN)
    assert exc.value.status_code == 400


def test_login_sucesso_retorna_token(store):
    svc = AuthService(store)
    svc.register_account(_ACCT, _ADMIN)
    token = svc.login("admin@x.io", "senha123")
    assert isinstance(token, str) and len(token) > 10


def test_login_senha_errada_levanta_401(store):
    svc = AuthService(store)
    svc.register_account(_ACCT, _ADMIN)
    with pytest.raises(HTTPException) as exc:
        svc.login("admin@x.io", "errada")
    assert exc.value.status_code == 401


def test_login_email_inexistente_levanta_401(store):
    svc = AuthService(store)
    with pytest.raises(HTTPException) as exc:
        svc.login("naoexiste@x.io", "qualquer")
    assert exc.value.status_code == 401


def test_create_user_vincula_a_account(store):
    svc = AuthService(store)
    account, _, _ = svc.register_account(_ACCT, _ADMIN)
    new_user_data = UserCreate(
        nome="Operador", email="op@x.io", tipo=TipoAgente.OPERADOR, senha="op123"
    )
    user = svc.create_user(account.id, new_user_data, RolePerfil.OPERADOR)
    assert user.account_id == account.id
    profile = store.profiles.find_one(user_id=user.id)
    assert profile.role == RolePerfil.OPERADOR


def test_create_user_email_duplicado_levanta_400(store):
    svc = AuthService(store)
    account, _, _ = svc.register_account(_ACCT, _ADMIN)
    data = UserCreate(nome="Op", email="admin@x.io", tipo=TipoAgente.OPERADOR, senha="x")
    with pytest.raises(HTTPException) as exc:
        svc.create_user(account.id, data, RolePerfil.OPERADOR)
    assert exc.value.status_code == 400
