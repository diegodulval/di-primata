from uuid import UUID

from fastapi import HTTPException, status

from app.core.auth import create_access_token, hash_password, verify_password
from app.models.enums import RolePerfil, TipoAgente
from app.models.user import Profile, User, UserCreate
from app.models.account import Account, AccountCreate
from app.repositories.store import Store


class AuthService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def register_account(self, account_data: AccountCreate, admin_data: UserCreate) -> tuple[Account, User, str]:
        if self.store.accounts.find_one(email=account_data.email):
            raise HTTPException(status_code=400, detail="Email já cadastrado")

        account = Account(**account_data.model_dump())
        self.store.accounts.save(account)

        user = User(
            account_id=account.id,
            nome=admin_data.nome,
            email=admin_data.email,
            tipo=TipoAgente.PRODUTOR_RURAL,
            senha_hash=hash_password(admin_data.senha),
        )
        self.store.users.save(user)

        profile = Profile(account_id=account.id, user_id=user.id, role=RolePerfil.ADMIN)
        self.store.profiles.save(profile)

        token = create_access_token(user.id, account.id, RolePerfil.ADMIN)
        return account, user, token

    def login(self, email: str, senha: str) -> str:
        user = self.store.users.find_one(email=email)
        if not user or not verify_password(senha, user.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
            )
        if not user.ativo:
            raise HTTPException(status_code=403, detail="Usuário inativo")

        profile = self.store.profiles.find_one(user_id=user.id, account_id=user.account_id)
        role = profile.role if profile else RolePerfil.OPERADOR
        return create_access_token(user.id, user.account_id, role)

    def create_user(self, account_id: UUID, data: UserCreate, role: RolePerfil) -> User:
        if self.store.users.find_one(email=data.email):
            raise HTTPException(status_code=400, detail="Email já cadastrado")

        user = User(
            account_id=account_id,
            nome=data.nome,
            email=data.email,
            tipo=data.tipo,
            senha_hash=hash_password(data.senha),
        )
        self.store.users.save(user)

        profile = Profile(account_id=account_id, user_id=user.id, role=role)
        self.store.profiles.save(profile)
        return user
