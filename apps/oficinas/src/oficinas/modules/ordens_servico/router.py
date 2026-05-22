import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.enums import StatusOS
from oficinas.core.security import requer_atendente_acima, requer_autenticado
from oficinas.modules.cadastros.models import Cliente
from oficinas.modules.ordens_servico.models import OrdemServico
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
from oficinas.shared.veiculo_global.models import Veiculo

router = APIRouter(prefix="/os", tags=["ordens_servico"])


async def _enrich(os: OrdemServico, db: AsyncSession) -> OSResponse:
    resp = OSResponse.model_validate(os)
    cliente = (await db.execute(
        select(Cliente.nome).where(Cliente.id == os.cliente_id)
    )).scalar_one_or_none()
    veiculo = (await db.execute(
        select(Veiculo.placa).where(Veiculo.id == os.veiculo_id)
    )).scalar_one_or_none()
    resp.cliente_nome = cliente
    resp.veiculo_placa = veiculo
    return resp


async def _enrich_lista(items: list[OrdemServico], db: AsyncSession) -> list[OSResponse]:
    if not items:
        return []
    cliente_ids = list({i.cliente_id for i in items})
    veiculo_ids = list({i.veiculo_id for i in items})

    clientes = {
        str(r.id): r.nome
        for r in (await db.execute(
            select(Cliente.id, Cliente.nome).where(Cliente.id.in_(cliente_ids))
        )).all()
    }
    veiculos = {
        str(r.id): r.placa
        for r in (await db.execute(
            select(Veiculo.id, Veiculo.placa).where(Veiculo.id.in_(veiculo_ids))
        )).all()
    }

    result = []
    for os in items:
        resp = OSResponse.model_validate(os)
        resp.cliente_nome = clientes.get(str(os.cliente_id))
        resp.veiculo_placa = veiculos.get(str(os.veiculo_id))
        result.append(resp)
    return result


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
    os = await OrdensServicoService(db).abrir(usuario.tenant_id, usuario.id, payload)
    return await _enrich(os, db)


@router.get(
    "",
    response_model=OSListResponse,
    summary="Listar OS do tenant. Filtre por ?status_os=, ?mecanico_id= e ?placa=",
)
async def listar_os(
    status_os: StatusOS | None = None,
    mecanico_id: uuid.UUID | None = None,
    placa: str | None = None,
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
):
    items = await OrdensServicoService(db).listar(
        usuario.tenant_id, status=status_os, mecanico_id=mecanico_id, placa=placa
    )
    enriched = await _enrich_lista(items, db)
    return OSListResponse(total=len(enriched), items=enriched)


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
    os = await OrdensServicoService(db).buscar(os_id, usuario.tenant_id)
    return await _enrich(os, db)


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
    os = await OrdensServicoService(db).atualizar_status(
        os_id, usuario.tenant_id, payload.novo_status
    )
    return await _enrich(os, db)


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
    os = await OrdensServicoService(db).fechar(os_id, usuario.tenant_id, payload)
    return await _enrich(os, db)


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
    os = await OrdensServicoService(db).cancelar(os_id, usuario.tenant_id)
    return await _enrich(os, db)
