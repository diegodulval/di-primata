import logging
from uuid import UUID

from fastapi import HTTPException, status

from auth.jwt import create_access_token, hash_password, verify_password
from core.models.enums import RolePerfil, TipoAgente
from core.models.user import Profile, User, UserCreate
from core.models.account import Account, AccountCreate
from producao.repositories.store import Store

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def register_account(self, account_data: AccountCreate, admin_data: UserCreate) -> tuple[Account, User, str]:
        logger.debug("Iniciando registro de conta: email=%s", account_data.email)

        if self.store.accounts.find_one(email=account_data.email):
            logger.info("Registro rejeitado — email já cadastrado: %s", account_data.email)
            raise HTTPException(status_code=400, detail="Email já cadastrado")

        account = Account(**account_data.model_dump())
        self.store.accounts.save(account)
        logger.debug("Conta criada: account_id=%s", account.id)

        user = User(
            account_id=account.id,
            nome=admin_data.nome,
            email=admin_data.email,
            tipo=TipoAgente.PRODUTOR_RURAL,
            senha_hash=hash_password(admin_data.senha),
        )
        self.store.users.save(user)
        logger.debug("Usuário admin criado: user_id=%s email=%s", user.id, user.email)

        profile = Profile(account_id=account.id, user_id=user.id, role=RolePerfil.ADMIN)
        self.store.profiles.save(profile)
        logger.debug("Perfil ADMIN criado: user_id=%s account_id=%s", user.id, account.id)

        token = create_access_token(user.id, account.id, RolePerfil.ADMIN)
        logger.info("Conta registrada com sucesso: account_id=%s user_id=%s", account.id, user.id)
        return account, user, token

    def login(self, email: str, senha: str) -> str:
        logger.debug("Tentativa de login: email=%s", email)

        user = self.store.users.find_one(email=email)
        if not user:
            logger.info("Login falhou — usuário não encontrado: email=%s", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
            )

        if not verify_password(senha, user.senha_hash):
            logger.info("Login falhou — senha incorreta: user_id=%s email=%s", user.id, email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
            )

        if not user.ativo:
            logger.info("Login bloqueado — usuário inativo: user_id=%s", user.id)
            raise HTTPException(status_code=403, detail="Usuário inativo")

        profile = self.store.profiles.find_one(user_id=user.id, account_id=user.account_id)
        role = profile.role if profile else RolePerfil.OPERADOR
        logger.debug("Perfil resolvido: user_id=%s role=%s (perfil_encontrado=%s)", user.id, role, profile is not None)

        token = create_access_token(user.id, user.account_id, role)
        logger.info("Login bem-sucedido: user_id=%s email=%s role=%s", user.id, email, role)
        return token

    def create_user(self, account_id: UUID, data: UserCreate, role: RolePerfil) -> User:
        logger.debug("Criando usuário: email=%s account_id=%s role=%s", data.email, account_id, role)

        if self.store.users.find_one(email=data.email):
            logger.info("Criação rejeitada — email já cadastrado: %s", data.email)
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

        logger.info("Usuário criado: user_id=%s email=%s role=%s", user.id, user.email, role)
        return user
