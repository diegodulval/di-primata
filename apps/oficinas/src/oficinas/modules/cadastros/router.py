import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.security import requer_admin, requer_atendente_acima
from oficinas.modules.cadastros.schemas import (
    ClienteCreate,
    ClienteResponse,
    ClienteUpdate,
    ClienteVeiculoCreate,
    ClienteVeiculoResponse,
    ClientesPaginados,
    ImportacaoClienteResponse,
    ImportacaoVeiculosResponse,
)
from oficinas.modules.cadastros.service import CadastroService

router = APIRouter(prefix="/clientes", tags=["cadastros"])


@router.post("/importar-veiculos-json", response_model=ImportacaoVeiculosResponse,
             summary="Importar vínculos cliente-veículo via JSON exportado do concorrente (ADMIN)")
async def importar_veiculos_json(
    arquivo: UploadFile,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    conteudo = await arquivo.read()
    try:
        resultado = await CadastroService(db).importar_veiculos_json(usuario.tenant_id, conteudo)
    except Exception as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return resultado


@router.post("/importar", response_model=ImportacaoClienteResponse,
             summary="Importar clientes via planilha XLSX (ADMIN)")
async def importar_clientes(
    arquivo: UploadFile,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    conteudo = await arquivo.read()
    try:
        resultado = await CadastroService(db).importar_clientes_xlsx(usuario.tenant_id, conteudo)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return resultado


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED,
             summary="Criar cliente (ATENDENTE/ADMIN)")
async def criar_cliente(
    payload: ClienteCreate,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).criar_cliente(usuario.tenant_id, payload)


@router.get("", response_model=ClientesPaginados,
            summary="Listar clientes. Filtros: ?q=, ?tipo_pessoa=, ?ativo=, ?uf=, ?page=, ?page_size=")
async def listar_clientes(
    q: str | None = None,
    tipo_pessoa: str | None = None,
    ativo: bool | None = None,
    uf: str | None = None,
    page: int = 1,
    page_size: int = 20,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    items, total = await CadastroService(db).listar_clientes(
        usuario.tenant_id, q=q, tipo_pessoa=tipo_pessoa, ativo=ativo, uf=uf,
        page=page, page_size=page_size,
    )
    return ClientesPaginados(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{cliente_id}", response_model=ClienteResponse,
            summary="Detalhar cliente (ATENDENTE/ADMIN)")
async def detalhar_cliente(
    cliente_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).buscar_cliente(cliente_id, usuario.tenant_id)


@router.patch("/{cliente_id}", response_model=ClienteResponse,
              summary="Atualizar dados do cliente (ATENDENTE/ADMIN)")
async def atualizar_cliente(
    cliente_id: uuid.UUID,
    payload: ClienteUpdate,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).atualizar_cliente(cliente_id, usuario.tenant_id, payload)


@router.get("/{cliente_id}/veiculos", response_model=list[ClienteVeiculoResponse],
            summary="Veículos vinculados ao cliente")
async def listar_veiculos_cliente(
    cliente_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).listar_veiculos_cliente(cliente_id, usuario.tenant_id)


@router.post("/{cliente_id}/veiculos", response_model=ClienteVeiculoResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Vincular veículo ao cliente")
async def vincular_veiculo(
    cliente_id: uuid.UUID,
    payload: ClienteVeiculoCreate,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).vincular_veiculo(
        cliente_id, payload.veiculo_id, usuario.tenant_id
    )


@router.delete("/{cliente_id}/veiculos/{veiculo_id}", response_model=ClienteVeiculoResponse,
               summary="Desassociar veículo do cliente")
async def desassociar_veiculo(
    cliente_id: uuid.UUID,
    veiculo_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await CadastroService(db).desassociar_veiculo(
        cliente_id, veiculo_id, usuario.tenant_id
    )
