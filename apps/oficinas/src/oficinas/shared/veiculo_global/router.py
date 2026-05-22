from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import get_raw_db, make_db
from oficinas.core.exceptions import NaoEncontrado
from oficinas.core.security import requer_atendente_acima, requer_autenticado
from oficinas.modules.cadastros.models import Cliente, ClienteVeiculo
from oficinas.modules.cadastros.schemas import ClienteResponse
from oficinas.shared.veiculo_global.schemas import VeiculoComHistorico, VeiculoCreate, VeiculoResponse
from oficinas.shared.veiculo_global.service import VeiculoService

router = APIRouter(prefix="/veiculos", tags=["veiculos"])


@router.get(
    "/{placa}",
    response_model=VeiculoComHistorico,
    summary="Buscar veículo por placa + histórico público",
)
async def buscar_veiculo(
    placa: str,
    _usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(get_raw_db),
):
    svc = VeiculoService(db)
    veiculo = await svc.buscar_por_placa(placa)
    historico = await svc.historico_publico(veiculo.id)
    return VeiculoComHistorico.model_validate(
        {**veiculo.__dict__, "historico_publico": historico}
    )


@router.get(
    "/{placa}/cliente-atual",
    response_model=ClienteResponse,
    summary="Retorna o cliente atual (dono ativo) do veículo neste tenant",
)
async def cliente_atual_do_veiculo(
    placa: str,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    veiculo = await VeiculoService(db).buscar_por_placa(placa)
    link = (
        await db.execute(
            select(ClienteVeiculo).where(
                ClienteVeiculo.veiculo_id == veiculo.id,
                ClienteVeiculo.ativo.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not link:
        raise NaoEncontrado(f"Nenhum cliente vinculado à placa {placa.upper()}")
    cliente = (
        await db.execute(select(Cliente).where(Cliente.id == link.cliente_id))
    ).scalar_one_or_none()
    if not cliente:
        raise NaoEncontrado(f"Cliente do vínculo não encontrado")
    return ClienteResponse.model_validate(cliente)


@router.post(
    "",
    response_model=VeiculoResponse,
    status_code=201,
    summary="Criar ou atualizar veículo por placa (ATENDENTE/ADMIN)",
)
async def upsert_veiculo(
    payload: VeiculoCreate,
    _usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(get_raw_db),
):
    return await VeiculoService(db).upsert(payload)
