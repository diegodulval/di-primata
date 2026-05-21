import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.security import requer_atendente_acima
from oficinas.modules.cadastros.schemas import (
    ClienteCreate,
    ClienteListResponse,
    ClienteResponse,
    ClienteUpdate,
    ClienteVeiculoCreate,
    ClienteVeiculoResponse,
)
from oficinas.modules.cadastros.service import CadastroService

router = APIRouter(prefix="/clientes", tags=["cadastros"])


@router.post(
    "",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar cliente (ATENDENTE/ADMIN)",
)
async def criar_cliente(
    payload: ClienteCreate,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).criar_cliente(usuario.tenant_id, payload)


@router.get(
    "",
    response_model=ClienteListResponse,
    summary="Listar clientes do tenant. Use ?q= para busca por nome, CPF ou telefone.",
)
async def listar_clientes(
    q: str | None = None,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    svc = CadastroService(db)
    items = (
        await svc.buscar_por_q(q, usuario.tenant_id)
        if q
        else await svc.listar_clientes(usuario.tenant_id)
    )
    return ClienteListResponse(total=len(items), items=items)


@router.get(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Detalhar cliente (ATENDENTE/ADMIN)",
)
async def detalhar_cliente(
    cliente_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).buscar_cliente(cliente_id, usuario.tenant_id)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar dados do cliente (ATENDENTE/ADMIN)",
)
async def atualizar_cliente(
    cliente_id: uuid.UUID,
    payload: ClienteUpdate,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).atualizar_cliente(cliente_id, usuario.tenant_id, payload)


@router.get(
    "/{cliente_id}/veiculos",
    response_model=list[ClienteVeiculoResponse],
    summary="Veículos vinculados ao cliente (histórico completo)",
)
async def listar_veiculos_cliente(
    cliente_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).listar_veiculos_cliente(cliente_id, usuario.tenant_id)


@router.post(
    "/{cliente_id}/veiculos",
    response_model=ClienteVeiculoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Vincular veículo ao cliente. Se o veículo tiver outro dono ativo, troca automaticamente.",
)
async def vincular_veiculo(
    cliente_id: uuid.UUID,
    payload: ClienteVeiculoCreate,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).vincular_veiculo(
        cliente_id, payload.veiculo_id, usuario.tenant_id
    )


@router.delete(
    "/{cliente_id}/veiculos/{veiculo_id}",
    response_model=ClienteVeiculoResponse,
    summary="Desassociar veículo do cliente (fecha vínculo ativo)",
)
async def desassociar_veiculo(
    cliente_id: uuid.UUID,
    veiculo_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).desassociar_veiculo(
        cliente_id, veiculo_id, usuario.tenant_id
    )
