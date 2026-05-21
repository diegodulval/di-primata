import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.jwt import TokenData, decode_token

bearer = HTTPBearer()
logger = logging.getLogger(__name__)


def get_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> TokenData:
    logger.debug("Extraindo token Bearer da requisição")
    try:
        token_data = decode_token(creds.credentials)
        logger.debug("Token aceito: user_id=%s role=%s", token_data.user_id, token_data.role)
        return token_data
    except ValueError as exc:
        logger.info("Token rejeitado: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_roles(*roles: str):
    def _check(token: TokenData = Depends(get_token)) -> TokenData:
        if token.role not in roles:
            logger.info(
                "Acesso negado: user_id=%s role=%s roles_necessários=%s",
                token.user_id,
                token.role,
                roles,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")
        logger.debug("Role autorizada: user_id=%s role=%s", token.user_id, token.role)
        return token

    return _check


def get_twilio_client(request: Request):
    """Retorna o Twilio Client singleton inicializado no lifespan, ou None se não configurado."""
    return getattr(request.app.state, "twilio_client", None)


def get_debounce_buffer(request: Request):
    """Retorna o DebounceBuffer singleton, ou None se DATABASE_URL não configurada."""
    return getattr(request.app.state, "debounce_buffer", None)


def get_rate_limiter(request: Request):
    """Retorna o FixedWindowRateLimiter singleton."""
    return getattr(request.app.state, "rate_limiter", None)
