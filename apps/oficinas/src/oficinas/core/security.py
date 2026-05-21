import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.config import settings
from oficinas.core.database import get_raw_db
from oficinas.core.enums import Perfil
from oficinas.core.exceptions import CredenciaisInvalidas

log = structlog.get_logger()

_ALGORITHM = "HS256"
_bearer = HTTPBearer()


# ─── Token ────────────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str        # usuario.id
    tenant_id: str
    perfil: str


def criar_token(usuario_id: uuid.UUID, tenant_id: uuid.UUID, perfil: Perfil) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub":       str(usuario_id),
        "tenant_id": str(tenant_id),
        "perfil":    str(perfil),
        "exp":       expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def _decodificar_token(token: str) -> TokenPayload:
    try:
        raw = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        return TokenPayload(**raw)
    except ExpiredSignatureError:
        raise CredenciaisInvalidas("Token expirado")
    except (JWTError, KeyError, ValueError):
        raise CredenciaisInvalidas("Token inválido")


# ─── Senha ────────────────────────────────────────────────────────────────────

def hash_senha(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verificar_senha(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


# ─── Depends: extrai usuário do token ─────────────────────────────────────────
# Importação tardia de models para evitar ciclo (security ← models ← database ← security).
# get_usuario_atual é montado com get_raw_db para não exigir RLS no lookup de auth.

async def get_usuario_atual(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_raw_db),
):
    """
    Decodifica o JWT e carrega o Usuario do banco.
    Injetado nos routers via Depends — não chamar diretamente.
    """
    from oficinas.modules.iam.models import Usuario

    try:
        payload = _decodificar_token(creds.credentials)
    except CredenciaisInvalidas as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    usuario = await db.get(Usuario, uuid.UUID(payload.sub))
    if not usuario or not usuario.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou não encontrado")

    log.debug("auth_ok", usuario_id=payload.sub, perfil=payload.perfil)
    return usuario


# ─── Guards de perfil ─────────────────────────────────────────────────────────

def requer_admin(usuario=Depends(get_usuario_atual)):
    if usuario.perfil != Perfil.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Requer perfil ADMIN")
    return usuario


def requer_atendente_acima(usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in (Perfil.ADMIN, Perfil.ATENDENTE):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Requer perfil ADMIN ou ATENDENTE",
        )
    return usuario


def requer_autenticado(usuario=Depends(get_usuario_atual)):
    """Qualquer perfil válido — só valida autenticação."""
    return usuario
