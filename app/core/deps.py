from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import TokenData, decode_token
from app.repositories.store import Store, get_store

bearer = HTTPBearer()


def get_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> TokenData:
    try:
        return decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def require_roles(*roles: str):
    def _check(token: TokenData = Depends(get_token)) -> TokenData:
        if token.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")
        return token
    return _check
