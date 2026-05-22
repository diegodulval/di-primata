import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.security import requer_atendente_acima
from oficinas.modules.vendas.schemas import ItemVendaResponse, VendaCreate, VendaResponse
from oficinas.modules.vendas.service import VendasService

router = APIRouter(prefix="/vendas", tags=["vendas"])


def _build_response(venda, itens) -> VendaResponse:
    resp = VendaResponse.model_validate(venda)
    resp.itens = [ItemVendaResponse.model_validate(i) for i in itens]
    return resp


@router.post("", response_model=VendaResponse, status_code=status.HTTP_201_CREATED,
             summary="Registrar venda PDV balcão (ATENDENTE/ADMIN)")
async def criar_venda(
    payload: VendaCreate,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    svc = VendasService(db)
    venda = await svc.criar(usuario.tenant_id, usuario.id, payload)
    itens = await svc.listar_itens(venda.id)
    return _build_response(venda, itens)


@router.get("", response_model=list[VendaResponse],
            summary="Listar vendas (ATENDENTE/ADMIN)")
async def listar_vendas(
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await VendasService(db).listar(usuario.tenant_id)


@router.get("/{venda_id}", response_model=VendaResponse,
            summary="Detalhar venda com itens (ATENDENTE/ADMIN)")
async def detalhar_venda(
    venda_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    svc = VendasService(db)
    venda = await svc.buscar(venda_id, usuario.tenant_id)
    itens = await svc.listar_itens(venda_id)
    return _build_response(venda, itens)
