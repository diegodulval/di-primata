from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import get_raw_db
from oficinas.core.exceptions import NaoEncontrado
from oficinas.core.security import requer_atendente_acima, requer_autenticado
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
