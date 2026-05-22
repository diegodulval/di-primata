import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from oficinas.core.config import settings
from oficinas.core.exceptions import (
    CredenciaisInvalidas,
    EmailJaCadastrado,
    EstoqueInsuficiente,
    MecanicoObrigatorio,
    NaoEncontrado,
    NFeJaImportada,
    OficinaDomainError,
    OSJaFechada,
    PlacaInvalida,
    RascunhoJaConfirmado,
    RascunhoPendente,
    TransicaoInvalida,
    UsuarioInativo,
    WhatsappJaCadastrado,
    WhatsappObrigatorioParaMecanico,
)

_log_level = logging.DEBUG if settings.app_env == "development" else logging.INFO
_app_logger = logging.getLogger("oficinas")
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


from oficinas.agente.webhook import router as webhook_router
from oficinas.modules.cadastros.router import router as cadastros_router
from oficinas.modules.estoque.router import entradas_router, fornecedores_router, produtos_router
from oficinas.modules.iam.router import router as auth_router, usuarios_router
from oficinas.modules.ordens_servico.router import router as os_router
from oficinas.modules.vendas.router import router as vendas_router
from oficinas.shared.veiculo_global.router import router as veiculos_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Oficinas iniciando...")
    yield
    logger.info("Oficinas encerrando...")


app = FastAPI(
    title="Di Mata — Oficinas",
    version="0.1.0",
    description="Gerenciamento de oficinas e manutenção",
    lifespan=lifespan,
    redirect_slashes=False,
)

_FRONTEND_URL = os.getenv("FRONTEND_URL", "")
_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    *([_FRONTEND_URL] if _FRONTEND_URL else []),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(veiculos_router)
app.include_router(cadastros_router)
app.include_router(produtos_router)
app.include_router(fornecedores_router)
app.include_router(entradas_router)
app.include_router(os_router)
app.include_router(vendas_router)
app.include_router(webhook_router)


# ─── Exception handlers ───────────────────────────────────────────────────────

_STATUS = {
    NaoEncontrado: 404,
    CredenciaisInvalidas: 401,
    UsuarioInativo: 403,
    EmailJaCadastrado: 409,
    WhatsappJaCadastrado: 409,
    NFeJaImportada: 409,
    RascunhoJaConfirmado: 409,
    OSJaFechada: 409,
    WhatsappObrigatorioParaMecanico: 422,
    PlacaInvalida: 422,
    EstoqueInsuficiente: 422,
    RascunhoPendente: 422,
    TransicaoInvalida: 422,
    MecanicoObrigatorio: 422,
}


@app.exception_handler(OficinaDomainError)
async def domain_error_handler(_: Request, exc: OficinaDomainError) -> JSONResponse:
    status_code = _STATUS.get(type(exc), 400)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "oficinas", "version": "0.1.0"}
