from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.models.account import AccountCreate
from core.models.user import UserCreate
from producao.repositories.store import Store, get_store
from producao.services.auth_service import AuthService

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    account: AccountCreate
    admin: UserCreate


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, store: Store = Depends(get_store)):
    svc = AuthService(store)
    _, _, token = svc.register_account(body.account, body.admin)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, store: Store = Depends(get_store)):
    svc = AuthService(store)
    token = svc.login(body.email, body.senha)
    return TokenResponse(access_token=token)
