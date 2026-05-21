import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from producao.config import settings
from producao.routers import accounts, auth, bff, cycles, events, lots, public, units, whatsapp

# Habilita DEBUG para todos os loggers app.* em desenvolvimento.
# Em produção mantém INFO para não expor dados sensíveis nos logs.
_log_level = logging.DEBUG if settings.app_env == "development" else logging.INFO
_app_logger = logging.getLogger("producao")
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
    from core.models.account import AccountCreate
    from core.models.enums import TipoAgente
    from core.models.user import UserCreate
    from producao.repositories.store import get_store
    from producao.services.auth_service import AuthService

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
            whatsapp_phone=settings.bootstrap_admin_whatsapp_phone or None,
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


def _init_twilio(app: FastAPI) -> None:
    from producao.config import settings as cfg

    if cfg.twilio_account_sid and cfg.twilio_auth_token:
        from twilio.rest import Client

        app.state.twilio_client = Client(cfg.twilio_account_sid, cfg.twilio_auth_token)
        logger.info("Twilio client inicializado | from=%s", cfg.twilio_whatsapp_from)
    else:
        app.state.twilio_client = None
        logger.warning("Twilio não configurado — envios serão simulados")


async def _init_db(_app: FastAPI) -> None:
    from core.db import pool as db_pool_module
    from producao.ingestion.debounce import DebounceBuffer
    from producao.ingestion.rate_limiter import FixedWindowRateLimiter

    _app.state.rate_limiter = FixedWindowRateLimiter(
        max_requests=settings.rate_limit_max,
        window_seconds=settings.rate_limit_window,
    )

    if settings.database_url:
        pool = await db_pool_module.create_pool(settings.database_url)
        _app.state.db_pool = pool
        _app.state.debounce_buffer = DebounceBuffer(pool, window_seconds=settings.debounce_window_seconds)
        logger.info("DB pool inicializado | url=%s", settings.database_url.split("@")[-1])
    else:
        _app.state.db_pool = None
        _app.state.debounce_buffer = DebounceBuffer(None, window_seconds=settings.debounce_window_seconds)
        logger.warning("DATABASE_URL não configurada — mensagens não serão persistidas na fila")


async def _close_db(_app: FastAPI) -> None:
    from core.db import pool as db_pool_module

    pool = getattr(_app.state, "db_pool", None)
    if pool:
        await db_pool_module.close_pool(pool)
        logger.info("DB pool encerrado")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _bootstrap_admin()
    _init_twilio(_app)
    await _init_db(_app)
    yield
    await _close_db(_app)
    _app.state.twilio_client = None


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
app.include_router(public.router,     prefix="/p",         tags=["public"])
app.include_router(whatsapp.router,   prefix="/whatsapp",  tags=["whatsapp"])
app.include_router(bff.router,        prefix="/bff",        tags=["bff"])


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/hello", tags=["infra"])
def hello():
    return {"message": "Hello, World!", "service": "Di Mata", "timestamp": "2026-05-03"}
