import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.enums import StatusItem
from oficinas.core.security import requer_admin, requer_atendente_acima
from oficinas.modules.estoque.rascunho_service import RascunhoService
from oficinas.modules.estoque.schemas import (
    EntradaNfeResponse,
    EntradaUpdate,
    FornecedorCreate,
    FornecedorResponse,
    FornecedorUpdate,
    ImportacaoFornecedorResponse,
    ImportacaoResponse,
    ItemEntradaResponse,
    ItemRascunhoResponse,
    MovimentacaoResponse,
    ProdutoCreate,
    ProdutoFornecedorResponse,
    ProdutoResponse,
    ProdutosPaginados,
    ProdutoUpdate,
    RascunhoResponse,
    VincularItemPayload,
)
from oficinas.modules.estoque.service import EstoqueService

produtos_router    = APIRouter(prefix="/produtos",    tags=["estoque"])
fornecedores_router = APIRouter(prefix="/fornecedores", tags=["estoque"])
entradas_router    = APIRouter(prefix="/entradas",    tags=["estoque"])


def _build_entrada_response(entrada, itens) -> EntradaNfeResponse:
    resp = EntradaNfeResponse.model_validate(entrada)
    resp.itens = [ItemEntradaResponse.model_validate(i) for i in itens]
    return resp


def _build_rascunho_response(rascunho, itens_com_produto) -> RascunhoResponse:
    item_responses = []
    for entry in itens_com_produto:
        if isinstance(entry, tuple):
            item, produto = entry
        else:
            item, produto = entry, None
        r = ItemRascunhoResponse.model_validate(item)
        if produto is not None:
            r.codigo_produto = produto.codigo
            r.marca_produto = produto.marca
        item_responses.append(r)
    resp = RascunhoResponse.model_validate(rascunho)
    resp.itens = item_responses
    resp.pendentes = sum(1 for r in item_responses if r.status_item == StatusItem.PENDENTE)
    return resp


# ─── Produtos ─────────────────────────────────────────────────────────────────

@produtos_router.post("/importar", response_model=ImportacaoResponse,
                      summary="Importar produtos via planilha XLSX (ADMIN)")
async def importar_produtos(
    arquivo: UploadFile,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    conteudo = await arquivo.read()
    try:
        resultado = await EstoqueService(db).importar_produtos_xlsx(usuario.tenant_id, conteudo)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return resultado


@produtos_router.post("", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED,
                      summary="Criar produto (ADMIN)")
async def criar_produto(
    payload: ProdutoCreate,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await EstoqueService(db).criar_produto(usuario.tenant_id, payload)


@produtos_router.get("", response_model=ProdutosPaginados,
                     summary="Listar produtos ativos. Use ?q=, ?page=, ?page_size=")
async def listar_produtos(
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    import math
    items, total = await EstoqueService(db).listar_produtos(usuario.tenant_id, q, page, page_size)
    return ProdutosPaginados(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@produtos_router.get("/marcas", response_model=list[str],
                     summary="Listar marcas distintas dos produtos ativos (ATENDENTE/ADMIN)")
async def listar_marcas(
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).listar_marcas(usuario.tenant_id)


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

@fornecedores_router.post("/importar", response_model=ImportacaoFornecedorResponse,
                           summary="Importar fornecedores via planilha XLSX (ADMIN)")
async def importar_fornecedores(
    arquivo: UploadFile,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    conteudo = await arquivo.read()
    try:
        resultado = await EstoqueService(db).importar_fornecedores_xlsx(usuario.tenant_id, conteudo)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return resultado


@fornecedores_router.post("", response_model=FornecedorResponse, status_code=status.HTTP_201_CREATED,
                           summary="Criar fornecedor (ADMIN)")
async def criar_fornecedor(
    payload: FornecedorCreate,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await EstoqueService(db).criar_fornecedor(usuario.tenant_id, payload)


@fornecedores_router.get("", response_model=list[FornecedorResponse],
                          summary="Listar fornecedores. Filtre por ?q=, ?ativo=, ?tipo_pessoa= (ATENDENTE/ADMIN)")
async def listar_fornecedores(
    q: str | None = None,
    ativo: bool | None = None,
    tipo_pessoa: str | None = None,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).listar_fornecedores(usuario.tenant_id, q=q, ativo=ativo, tipo_pessoa=tipo_pessoa)


@fornecedores_router.get("/{fornecedor_id}", response_model=FornecedorResponse,
                          summary="Detalhar fornecedor (ATENDENTE/ADMIN)")
async def detalhar_fornecedor(
    fornecedor_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).buscar_fornecedor(fornecedor_id, usuario.tenant_id)


@fornecedores_router.get("/{fornecedor_id}/produtos", response_model=list[ProdutoFornecedorResponse],
                          summary="Produtos mapeados ao fornecedor (ATENDENTE/ADMIN)")
async def listar_produtos_fornecedor(
    fornecedor_id: uuid.UUID,
    q: str | None = None,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    return await EstoqueService(db).listar_produtos_fornecedor(fornecedor_id, usuario.tenant_id, q=q)


@fornecedores_router.patch("/{fornecedor_id}", response_model=FornecedorResponse,
                            summary="Atualizar fornecedor (ADMIN)")
async def atualizar_fornecedor(
    fornecedor_id: uuid.UUID,
    payload: FornecedorUpdate,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await EstoqueService(db).atualizar_fornecedor(fornecedor_id, usuario.tenant_id, payload)


# ─── Entradas NF-e — rascunho ─────────────────────────────────────────────────

@entradas_router.post("/xml", response_model=RascunhoResponse, status_code=status.HTTP_201_CREATED,
                      summary="Importar NF-e via XML — cria rascunho para revisão (ADMIN)")
async def importar_nfe(
    arquivo: UploadFile,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    conteudo = await arquivo.read()
    rascunho, itens = await RascunhoService(db).criar_rascunho(conteudo, usuario.tenant_id)
    return _build_rascunho_response(rascunho, itens)


@entradas_router.get("/rascunhos", response_model=list[RascunhoResponse],
                     summary="Listar rascunhos de NF-e (ATENDENTE/ADMIN)")
async def listar_rascunhos(
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    svc = RascunhoService(db)
    rascunhos_com_forn = await svc.listar_com_fornecedor(usuario.tenant_id)
    result = []
    for r, fornecedor in rascunhos_com_forn:
        itens = await svc.carregar_itens_com_produto(r.id)
        resp = _build_rascunho_response(r, itens)
        resp.fornecedor_nome = fornecedor.razao_social if fornecedor else None
        result.append(resp)
    return result


@entradas_router.get("/rascunhos/{rascunho_id}", response_model=RascunhoResponse,
                     summary="Detalhar rascunho com itens (ATENDENTE/ADMIN)")
async def detalhar_rascunho(
    rascunho_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    svc = RascunhoService(db)
    rascunho = await svc.buscar(rascunho_id, usuario.tenant_id)
    itens = await svc.carregar_itens_com_produto(rascunho_id)
    return _build_rascunho_response(rascunho, itens)


@entradas_router.patch(
    "/rascunhos/{rascunho_id}/itens/{item_id}",
    response_model=ItemRascunhoResponse,
    summary="Vincular item a produto existente ou criar novo produto (ADMIN)",
)
async def vincular_item_rascunho(
    rascunho_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: VincularItemPayload,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await RascunhoService(db).vincular_item(rascunho_id, item_id, usuario.tenant_id, payload)


@entradas_router.post(
    "/rascunhos/{rascunho_id}/confirmar",
    response_model=EntradaNfeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar rascunho — gera entrada e movimenta estoque (ADMIN)",
)
async def confirmar_rascunho(
    rascunho_id: uuid.UUID,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    return await RascunhoService(db).confirmar(rascunho_id, usuario.tenant_id)


@entradas_router.delete(
    "/rascunhos/{rascunho_id}",
    response_model=RascunhoResponse,
    summary="Cancelar rascunho (ADMIN)",
)
async def cancelar_rascunho(
    rascunho_id: uuid.UUID,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    svc = RascunhoService(db)
    rascunho = await svc.cancelar(rascunho_id, usuario.tenant_id)
    itens = await svc.carregar_itens_com_produto(rascunho_id)
    return _build_rascunho_response(rascunho, itens)


# ─── Entradas NF-e — pós-confirmação ─────────────────────────────────────────

@entradas_router.get(
    "/{entrada_id}",
    response_model=EntradaNfeResponse,
    summary="Detalhar entrada com itens (ATENDENTE/ADMIN)",
)
async def detalhar_entrada(
    entrada_id: uuid.UUID,
    usuario=Depends(requer_atendente_acima),
    db: AsyncSession = Depends(make_db(requer_atendente_acima)),
):
    svc = EstoqueService(db)
    entrada = await svc.buscar_entrada(entrada_id, usuario.tenant_id)
    itens = await svc.listar_itens_entrada(entrada_id)
    return _build_entrada_response(entrada, itens)


@entradas_router.patch(
    "/{entrada_id}",
    response_model=EntradaNfeResponse,
    summary="Salvar datas e processar entrada para financeiro (ADMIN)",
)
async def processar_entrada(
    entrada_id: uuid.UUID,
    payload: EntradaUpdate,
    usuario=Depends(requer_admin),
    db: AsyncSession = Depends(make_db(requer_admin)),
):
    svc = EstoqueService(db)
    entrada = await svc.processar_entrada(
        entrada_id, usuario.tenant_id, payload.data_entrada, payload.itens
    )
    itens = await svc.listar_itens_entrada(entrada_id)
    return _build_entrada_response(entrada, itens)
