from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from oficinas.core.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    # postgresql+asyncpg:// já é o formato correto para SQLAlchemy async
    async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(async_url, echo=settings.app_env == "development")


engine = _make_engine(settings.database_url) if settings.database_url else None

_SessionLocal: async_sessionmaker[AsyncSession] | None = (
    async_sessionmaker(engine, expire_on_commit=False) if engine else None
)


async def _open_session() -> AsyncGenerator[AsyncSession, None]:
    if _SessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada")
    async with _SessionLocal() as session:
        yield session


# ─── get_raw_db ───────────────────────────────────────────────────────────────
# Sessão sem RLS: usada no login e em operações que não têm tenant context.
# usuario não está sob RLS, então login funciona sem SET LOCAL.

async def get_raw_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _open_session():
        yield session


# ─── get_db ───────────────────────────────────────────────────────────────────
# Sessão com RLS: seta app.current_tenant antes de qualquer query.
# Todos os endpoints autenticados usam este Depends.
# FORCE ROW LEVEL SECURITY garante que nem o owner da tabela bypassa.

async def get_db(usuario=None) -> AsyncGenerator[AsyncSession, None]:
    """
    Fábrica de sessão com RLS.
    Uso nos routers:
        db: AsyncSession = Depends(make_db(requer_admin))
    Ou diretamente quando o usuario já foi resolvido.
    """
    async for session in _open_session():
        if usuario is not None:
            await session.execute(
                text(f"SET LOCAL app.current_tenant = '{usuario.tenant_id}'")
            )
        yield session


def make_db(auth_dep):
    """
    Helper para compor o Depends de sessão + autenticação em um único objeto.

    Uso no router:
        @router.get("/clientes")
        async def listar(
            usuario=Depends(requer_atendente_acima),
            db: AsyncSession = Depends(make_db(requer_atendente_acima)),
        ):
            ...

    Internamente monta uma dependência que:
      1. Extrai o usuario via auth_dep
      2. Abre sessão e seta SET LOCAL app.current_tenant
    """
    from fastapi import Depends

    async def _dep(usuario=Depends(auth_dep)) -> AsyncGenerator[AsyncSession, None]:
        async for session in get_db(usuario):
            yield session

    return _dep
