from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.security import requer_autenticado
from oficinas.modules.dashboard.schemas import DashboardResponse
from oficinas.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/me", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse, summary="Resumo operacional e financeiro")  # noqa: E501
async def get_dashboard(
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
) -> DashboardResponse:
    return await DashboardService(db).get()
