import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import get_raw_db, make_db
from oficinas.core.exceptions import (
    CredenciaisInvalidas,
    EmailJaCadastrado,
    NaoEncontrado,
    UsuarioInativo,
    WhatsappJaCadastrado,
    WhatsappObrigatorioParaMecanico,
)
from oficinas.core.security import requer_admin, requer_autenticado
from oficinas.modules.iam.schemas import (
    LoginRequest,
    TokenResponse,
    TrocarSenhaRequest,
    UsuarioCreate,
    UsuarioListResponse,
    UsuarioResponse,
    UsuarioSimples,
    UsuarioUpdate,
)
from oficinas.modules.iam.service import IamService

router = APIRouter(prefix="/auth", tags=["iam"])
usuarios_router = APIRouter(prefix="/usuarios", tags=["iam"])


# ─── Auth ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_raw_db),   # sem RLS — usuario não é tenant-scoped
):
    try:
        token = await IamService(db).login(payload)
    except CredenciaisInvalidas as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except UsuarioInativo as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))

    # Decodifica perfil para incluir na resposta sem hit extra no banco
    from jose import jwt as _jwt
    from oficinas.core.config import settings
    from oficinas.core.enums import Perfil
    raw = _jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    return TokenResponse(access_token=token, perfil=Perfil(raw["perfil"]))


# ─── Usuários — admin gerencia ─────────────────────────────────────────────────

@usuarios_router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário (ADMIN)",
)
async def criar_usuario(
    payload: UsuarioCreate,
    admin=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    try:
        usuario = await IamService(db).criar_usuario(admin.tenant_id, payload)
    except (EmailJaCadastrado, WhatsappJaCadastrado, WhatsappObrigatorioParaMecanico) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    return usuario


@usuarios_router.get(
    "/",
    response_model=UsuarioListResponse,
    summary="Listar usuários do tenant (ADMIN)",
)
async def listar_usuarios(
    admin=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    items = await IamService(db).listar_usuarios(admin.tenant_id)
    return UsuarioListResponse(total=len(items), items=items)


@usuarios_router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Perfil do usuário autenticado",
)
async def meu_perfil(usuario=Depends(requer_autenticado)):
    return usuario


@usuarios_router.patch(
    "/me/senha",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Trocar a própria senha",
)
async def trocar_minha_senha(
    payload: TrocarSenhaRequest,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    try:
        await IamService(db).trocar_senha(usuario, payload.senha_atual, payload.nova_senha)
    except CredenciaisInvalidas as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@usuarios_router.get(
    "/ativos",
    response_model=list[UsuarioSimples],
    summary="Lista simplificada de usuários ativos do tenant (qualquer autenticado)",
)
async def listar_usuarios_ativos(
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    items = await IamService(db).listar_usuarios_ativos(usuario.tenant_id)
    return [UsuarioSimples.model_validate(u) for u in items]


@usuarios_router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Detalhe de um usuário (ADMIN)",
)
async def detalhar_usuario(
    usuario_id: uuid.UUID,
    admin=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    try:
        return await IamService(db).buscar_usuario(usuario_id, admin.tenant_id)
    except NaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@usuarios_router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Atualizar usuário (ADMIN) — nome, perfil, whatsapp, ativar/desativar",
)
async def atualizar_usuario(
    usuario_id: uuid.UUID,
    payload: UsuarioUpdate,
    admin=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    try:
        return await IamService(db).atualizar_usuario(usuario_id, admin.tenant_id, payload)
    except NaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except WhatsappObrigatorioParaMecanico as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@usuarios_router.delete(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Desativar usuário (ADMIN) — soft-delete",
)
async def desativar_usuario(
    usuario_id: uuid.UUID,
    admin=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    try:
        return await IamService(db).desativar_usuario(usuario_id, admin.tenant_id)
    except NaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
