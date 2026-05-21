import uuid

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.security import requer_admin, requer_atendente_acima
from oficinas.modules.estoque.schemas import (
    EntradaNfeResponse,
    FornecedorCreate,
    FornecedorResponse,
    MovimentacaoResponse,
    ProdutoCreate,
    ProdutoResponse,
    ProdutoUpdate,
)
from oficinas.modules.estoque.service import EstoqueService

produtos_router    = APIRouter(prefix="/produtos",    tags=["estoque"])
fornecedores_router = APIRouter(prefix="/fornecedores", tags=["estoque"])
entradas_router    = APIRouter(prefix="/entradas",    tags=["estoque"])


# ─── Produtos ─────────────────────────────────────────────────────────────────

@produtos_router.post("", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED,
                      summary="Criar produto (ADMIN)")
async def criar_produto(
    payload: ProdutoCreate,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await EstoqueService(db).criar_produto(usuario.tenant_id, payload)


@produtos_router.get("", response_model=list[ProdutoResponse],
                     summary="Listar produtos ativos. Use ?q= para busca.")
async def listar_produtos(
    q: str | None = None,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).listar_produtos(usuario.tenant_id, q)


@produtos_router.get("/{produto_id}", response_model=ProdutoResponse,
                     summary="Detalhar produto (ATENDENTE/ADMIN)")
async def detalhar_produto(
    produto_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).buscar_produto(produto_id, usuario.tenant_id)


@produtos_router.patch("/{produto_id}", response_model=ProdutoResponse,
                       summary="Atualizar produto (ADMIN)")
async def atualizar_produto(
    produto_id: uuid.UUID,
    payload: ProdutoUpdate,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await EstoqueService(db).atualizar_produto(produto_id, usuario.tenant_id, payload)


@produtos_router.get("/{produto_id}/movimentacoes", response_model=list[MovimentacaoResponse],
                     summary="Histórico de movimentações do produto (ATENDENTE/ADMIN)")
async def movimentacoes_produto(
    produto_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).listar_movimentacoes(produto_id, usuario.tenant_id)


# ─── Fornecedores ─────────────────────────────────────────────────────────────

@fornecedores_router.post("", response_model=FornecedorResponse, status_code=status.HTTP_201_CREATED,
                           summary="Criar fornecedor (ADMIN)")
async def criar_fornecedor(
    payload: FornecedorCreate,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await EstoqueService(db).criar_fornecedor(usuario.tenant_id, payload)


@fornecedores_router.get("", response_model=list[FornecedorResponse],
                          summary="Listar fornecedores (ATENDENTE/ADMIN)")
async def listar_fornecedores(
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).listar_fornecedores(usuario.tenant_id)


@fornecedores_router.get("/{fornecedor_id}", response_model=FornecedorResponse,
                          summary="Detalhar fornecedor (ATENDENTE/ADMIN)")
async def detalhar_fornecedor(
    fornecedor_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).buscar_fornecedor(fornecedor_id, usuario.tenant_id)


# ─── Entradas NF-e ────────────────────────────────────────────────────────────

@entradas_router.post("/xml", response_model=EntradaNfeResponse, status_code=status.HTTP_201_CREATED,
                      summary="Importar NF-e via XML (ADMIN)")
async def importar_nfe(
    arquivo: UploadFile,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    conteudo = await arquivo.read()
    return await EstoqueService(db).processar_entrada_xml(conteudo, usuario.tenant_id)
