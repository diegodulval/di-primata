import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, accounts, units, cycles, events, lots, public

# Habilita DEBUG para todos os loggers app.* em desenvolvimento.
# Em produção mantém INFO para não expor dados sensíveis nos logs.
_log_level = logging.DEBUG if settings.app_env == "development" else logging.INFO
_app_logger = logging.getLogger("app")
_app_logger.setLevel(_log_level)
if not _app_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    _app_logger.addHandler(_handler)

logger = logging.getLogger(__name__)


def _bootstrap_admin() -> None:
    from app.models.account import AccountCreate
    from app.models.enums import TipoAgente
    from app.models.user import UserCreate
    from app.repositories.store import get_store
    from app.services.auth_service import AuthService

    store = get_store()
    if store.accounts.list_all():
        logger.debug("Bootstrap: contas já existem, pulando criação do admin")
        return

    logger.info(
        "Bootstrap: nenhuma conta encontrada — criando admin padrão (email=%s)",
        settings.bootstrap_admin_email,
    )
    svc = AuthService(store)
    svc.register_account(
        AccountCreate(
            nome="Di Mata",
            documento="00.000.000/0001-00",
            email=settings.bootstrap_admin_email,
            setor_primario="Plataforma",
        ),
        UserCreate(
            nome=settings.bootstrap_admin_nome,
            email=settings.bootstrap_admin_email,
            tipo=TipoAgente.ADMIN_PLATAFORMA,
            senha=settings.bootstrap_admin_senha,
        ),
    )
    senha_hint = settings.bootstrap_admin_senha if settings.app_env == "development" else "***"
    logger.info(
        "Bootstrap admin criado | email=%s senha=%s",
        settings.bootstrap_admin_email,
        senha_hint,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _bootstrap_admin()
    yield


app = FastAPI(
    title="Di Mata",
    version="0.1.0",
    description="Plataforma de rastreabilidade de cadeia produtiva",
    lifespan=lifespan,
)

_FRONTEND_URL = os.getenv("FRONTEND_URL", "")
_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    *([_FRONTEND_URL] if _FRONTEND_URL else []),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/auth",    tags=["auth"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(units.router,    prefix="/units",   tags=["units"])
app.include_router(cycles.router,   prefix="/cycles",  tags=["cycles"])
app.include_router(events.router,   prefix="/cycles",  tags=["events"])
app.include_router(lots.router,     prefix="/cycles",  tags=["lots"])
app.include_router(public.router,   prefix="/p",       tags=["public"])


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/hello", tags=["infra"])
def hello():
    return {"message": "Hello, World!", "service": "Di Mata", "timestamp": "2026-05-03"}
