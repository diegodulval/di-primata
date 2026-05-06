import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt as _bcrypt
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

ALGORITHM = "HS256"
logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    user_id: UUID
    account_id: UUID
    role: str


def hash_password(plain: str) -> str:
    logger.debug("Gerando hash de senha")
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    logger.debug("Verificando senha")
    try:
        result = _bcrypt.checkpw(plain.encode(), hashed.encode())
        logger.debug("Verificação de senha: %s", "ok" if result else "falhou")
        return result
    except (ValueError, TypeError) as exc:
        logger.warning("Erro bcrypt checkpw: %s", exc)
        return False


def create_access_token(user_id: UUID, account_id: UUID, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "account_id": str(account_id),
        "role": str(role),
        "exp": expire,
    }
    logger.debug(
        "Criando token: user_id=%s account_id=%s role=%s expira=%s",
        user_id,
        account_id,
        role,
        expire.isoformat(),
    )
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenData:
    logger.debug("Decodificando token JWT")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        data = TokenData(
            user_id=UUID(payload["sub"]),
            account_id=UUID(payload["account_id"]),
            role=payload["role"],
        )
        logger.debug(
            "Token válido: user_id=%s account_id=%s role=%s",
            data.user_id,
            data.account_id,
            data.role,
        )
        return data
    except ExpiredSignatureError as exc:
        logger.info("Token expirado: %s", exc)
        raise ValueError("Token expirado") from exc
    except (JWTError, KeyError, ValueError) as exc:
        logger.warning("Falha ao decodificar token: %s | tipo=%s", exc, type(exc).__name__)
        raise ValueError("Token inválido") from exc
