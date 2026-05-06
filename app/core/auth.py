from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt as _bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

ALGORITHM = "HS256"


class TokenData(BaseModel):
    user_id: UUID
    account_id: UUID
    role: str


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: UUID, account_id: UUID, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "account_id": str(account_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return TokenData(
            user_id=UUID(payload["sub"]),
            account_id=UUID(payload["account_id"]),
            role=payload["role"],
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise ValueError("Token inválido") from exc
