from fastapi import APIRouter, Depends

from auth.jwt import TokenData
from auth.dependencies import get_token
from core.models.account import Account, AccountUpdate
from core.models.enums import RolePerfil
from core.models.user import User, UserCreate
from producao.repositories.store import Store, get_store
from producao.services.auth_service import AuthService

router = APIRouter()


@router.get("/me", response_model=Account)
def get_me(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    account = store.accounts.get(token.account_id)
    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Account não encontrada")
    return account


@router.patch("/me", response_model=Account)
def update_me(
    body: AccountUpdate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    account = store.accounts.get(token.account_id)
    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Account não encontrada")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(account, field, value)
    store.accounts.save(account)
    return account


@router.post("/users", response_model=User, status_code=201)
def create_user(
    body: UserCreate,
    role: RolePerfil = RolePerfil.OPERADOR,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = AuthService(store)
    return svc.create_user(token.account_id, body, role)


@router.get("/users", response_model=list[User])
def list_users(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    users = store.users.list_by(account_id=token.account_id)
    for u in users:
        u.senha_hash = "***"
    return users
