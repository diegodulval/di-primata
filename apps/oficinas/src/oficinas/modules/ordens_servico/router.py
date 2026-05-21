import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.enums import StatusOS
from oficinas.core.security import requer_atendente_acima, requer_autenticado
from oficinas.modules.ordens_servico.schemas import (
    AtualizarStatusOS,
    FecharOS,
    ItemOSAdd,
    ItemOSResponse,
    OSCreate,
    OSListResponse,
    OSResponse,
)
from oficinas.modules.ordens_servico.service import OrdensServicoService

router = APIRouter(prefix="/os", tags=["ordens_servico"])


@router.post(
    "",
    response_model=OSResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir OS (qualquer perfil autenticado)",
)
async def abrir_os(
    payload: OSCreate,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    return await OrdensServicoService(db).abrir(usuario.tenant_id, usuario.id, payload)


@router.get(
    "",
    response_model=OSListResponse,
    summary="Listar OS do tenant. Filtre por ?status_os= e ?mecanico_id=",
)
async def listar_os(
    status_os: StatusOS | None = None,
    mecanico_id: uuid.UUID | None = None,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    items = await OrdensServicoService(db).listar(
        usuario.tenant_id, status=status_os, mecanico_id=mecanico_id
    )
    return OSListResponse(total=len(items), items=items)


@router.get(
    "/{os_id}",
    response_model=OSResponse,
    summary="Detalhar OS",
)
async def detalhar_os(
    os_id: uuid.UUID,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    return await OrdensServicoService(db).buscar(os_id, usuario.tenant_id)


@router.get(
    "/{os_id}/itens",
    response_model=list[ItemOSResponse],
    summary="Listar itens da OS",
)
async def listar_itens_os(
    os_id: uuid.UUID,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    return await OrdensServicoService(db).listar_itens(os_id, usuario.tenant_id)


@router.post(
    "/{os_id}/itens",
    response_model=ItemOSResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item (peça ou serviço) à OS",
)
async def adicionar_item(
    os_id: uuid.UUID,
    payload: ItemOSAdd,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    return await OrdensServicoService(db).adicionar_item(os_id, usuario.tenant_id, payload)


@router.delete(
    "/{os_id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover item da OS (libera estoque se PECA)",
)
async def remover_item(
    os_id: uuid.UUID,
    item_id: uuid.UUID,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    await OrdensServicoService(db).remover_item(os_id, item_id, usuario.tenant_id)


@router.patch(
    "/{os_id}/status",
    response_model=OSResponse,
    summary="Avançar status (ABERTA↔EM_EXECUCAO↔AGUARDANDO_PECA)",
)
async def atualizar_status(
    os_id: uuid.UUID,
    payload: AtualizarStatusOS,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    return await OrdensServicoService(db).atualizar_status(
        os_id, usuario.tenant_id, payload.novo_status
    )


@router.post(
    "/{os_id}/fechar",
    response_model=OSResponse,
    summary="Fechar OS: converte reservas em saídas e registra histórico do veículo (ATENDENTE/ADMIN)",
)
async def fechar_os(
    os_id: uuid.UUID,
    payload: FecharOS,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await OrdensServicoService(db).fechar(os_id, usuario.tenant_id, payload)


@router.post(
    "/{os_id}/cancelar",
    response_model=OSResponse,
    summary="Cancelar OS: libera todas as peças reservadas (ATENDENTE/ADMIN)",
)
async def cancelar_os(
    os_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await OrdensServicoService(db).cancelar(os_id, usuario.tenant_id)
