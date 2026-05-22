import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oficinas.core.enums import StatusItem, StatusRascunho
from oficinas.core.exceptions import (
    NaoEncontrado,
    NFeJaImportada,
    RascunhoJaConfirmado,
    RascunhoPendente,
)
from oficinas.modules.estoque.models import (
    EntradaNfe,
    Fornecedor,
    ItemRascunhoEntrada,
    MapeamentoFornecedorProduto,
    Produto,
    RascunhoEntrada,
)
from oficinas.modules.estoque.rascunho_service import RascunhoService
from oficinas.modules.estoque.schemas import VincularItemPayload
from oficinas.modules.estoque.tests.conftest import resultado_com, resultado_lista, resultado_vazio

# ─── Fixtures ─────────────────────────────────────────────────────────────────

_XML_SIMPLES = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35231212345678000195550010000001231000000001">
      <ide><nNF>42</nNF><serie>1</serie><dhEmi>2024-04-28T10:00:00-03:00</dhEmi></ide>
      <emit><CNPJ>12345678000195</CNPJ><xNome>Distribuidora LTDA</xNome></emit>
      <det nItem="1">
        <prod>
          <cProd>FLT001</cProd>
          <xProd>FILTRO DE OLEO MANN</xProd>
          <NCM>84212300</NCM>
          <qCom>10.000</qCom>
          <vUnCom>25.50</vUnCom>
        </prod>
        <imposto><ICMS><ICMS00><pICMS>12.00</pICMS></ICMS00></ICMS></imposto>
      </det>
      <total><ICMSTot><vNF>255.00</vNF></ICMSTot></total>
    </infNFe>
  </NFe>
</nfeProc>"""

_XML_COM_CODIGO_REF = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35231212345678000195550010000001231000000002">
      <ide><nNF>43</nNF><serie>1</serie><dhEmi>2024-04-28T10:00:00-03:00</dhEmi></ide>
      <emit><CNPJ>12345678000195</CNPJ><xNome>Distribuidora LTDA</xNome></emit>
      <det nItem="1">
        <prod>
          <cProd>13646</cProd>
          <xProd>32208 AMORTECEDOR DIANT SUPER PLUS</xProd>
          <cEAN>7891234567890</cEAN>
          <NCM>87089900</NCM>
          <qCom>2.000</qCom>
          <vUnCom>150.00</vUnCom>
        </prod>
      </det>
      <total><ICMSTot><vNF>300.00</vNF></ICMSTot></total>
    </infNFe>
  </NFe>
</nfeProc>"""


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    vazio = MagicMock()
    vazio.scalar_one_or_none.return_value = None
    vazio.scalars.return_value.all.return_value = []
    db.execute.return_value = vazio
    return db


def _fornecedor(tenant_id: uuid.UUID) -> Fornecedor:
    return Fornecedor(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        razao_social="Distribuidora LTDA",
        cnpj="12345678000195",
    )


def _rascunho(tenant_id: uuid.UUID, status: str = StatusRascunho.PENDENTE) -> RascunhoEntrada:
    return RascunhoEntrada(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        fornecedor_id=uuid.uuid4(),
        chave_nfe="35231212345678000195550010000001231000000001",
        numero_nf="42",
        data_emissao=None,
        valor_total=Decimal("255.00"),
        status=status,
    )


def _item_rascunho(rascunho_id: uuid.UUID, status: str = StatusItem.PENDENTE) -> ItemRascunhoEntrada:
    return ItemRascunhoEntrada(
        id=uuid.uuid4(),
        rascunho_id=rascunho_id,
        produto_id=None,
        codigo_fornecedor="FLT001",
        codigo_ref=None,
        ean=None,
        descricao_nfe="FILTRO DE OLEO MANN",
        ncm="84212300",
        quantidade=Decimal("10.000"),
        preco_unitario=Decimal("25.50"),
        icms=Decimal("12.00"),
        ipi=Decimal("0"),
        status_item=status,
    )


def _produto(tenant_id: uuid.UUID, codigo: str = "32208") -> Produto:
    return Produto(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo=codigo,
        descricao="AMORTECEDOR DIANT",
        ncm="87089900",
        preco_custo=Decimal("100.00"),
        preco_venda=Decimal("150.00"),
        estoque_atual=Decimal("5.000"),
        estoque_minimo=Decimal("0"),
        estoque_maximo=Decimal("0"),
        ativo=True,
    )


# ─── criar_rascunho ───────────────────────────────────────────────────────────

async def test_criar_rascunho_item_sem_match_fica_pendente(mock_db, tenant_id):
    # EntradaNfe check → None, Fornecedor → None (cria novo), MapeamentoFornecedorProduto → None
    # sem codigo_ref, sem EAN → PENDENTE
    mock_db.execute.side_effect = [resultado_vazio(), resultado_vazio(), resultado_vazio()]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_XML_SIMPLES, tenant_id)

    assert len(itens) == 1
    assert itens[0].status_item == StatusItem.PENDENTE
    assert itens[0].produto_id is None


async def test_criar_rascunho_auto_vincula_por_codigo_ref(mock_db, tenant_id):
    produto = _produto(tenant_id, codigo="32208")
    # EntradaNfe check → None, Fornecedor → None (cria), MapeamentoFornecedorProduto → None,
    # Produto by codigo_ref "32208" → produto
    mock_db.execute.side_effect = [
        resultado_vazio(),   # EntradaNfe
        resultado_vazio(),   # Fornecedor (cria novo)
        resultado_vazio(),   # MapeamentoFornecedorProduto
        resultado_com(produto),  # Produto by codigo_ref
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_XML_COM_CODIGO_REF, tenant_id)

    assert itens[0].status_item == StatusItem.AUTO_VINCULADO
    assert itens[0].produto_id == produto.id


async def test_criar_rascunho_auto_vincula_por_ean(mock_db, tenant_id):
    fornecedor = _fornecedor(tenant_id)
    produto = _produto(tenant_id)
    produto.ean = "7891234567890"
    # Fornecedor select returns existing (id set), so fornecedor_id is not None
    # MapeamentoFornecedorProduto → None, Produto by codigo_ref → None, Produto by EAN → produto
    mock_db.execute.side_effect = [
        resultado_vazio(),       # EntradaNfe
        resultado_com(fornecedor),  # Fornecedor (found, id is set)
        resultado_vazio(),       # MapeamentoFornecedorProduto
        resultado_vazio(),       # Produto by codigo_ref
        resultado_com(produto),  # Produto by EAN
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_XML_COM_CODIGO_REF, tenant_id)

    assert itens[0].status_item == StatusItem.AUTO_VINCULADO
    assert itens[0].produto_id == produto.id


async def test_criar_rascunho_auto_vincula_por_mapeamento(mock_db, tenant_id):
    fornecedor = _fornecedor(tenant_id)
    produto = _produto(tenant_id)
    mapeamento = MapeamentoFornecedorProduto(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        fornecedor_id=fornecedor.id,
        codigo_fornecedor="13646",
        produto_id=produto.id,
    )
    mock_db.execute.side_effect = [
        resultado_vazio(),          # EntradaNfe
        resultado_com(fornecedor),  # Fornecedor (found, id is set)
        resultado_com(mapeamento),  # MapeamentoFornecedorProduto → match
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_XML_COM_CODIGO_REF, tenant_id)

    assert itens[0].status_item == StatusItem.AUTO_VINCULADO
    assert itens[0].produto_id == produto.id


async def test_criar_rascunho_levanta_nfe_ja_importada(mock_db, tenant_id):
    entrada_existente = EntradaNfe(id=uuid.uuid4(), tenant_id=tenant_id)
    mock_db.execute.return_value = resultado_com(entrada_existente)

    with pytest.raises(NFeJaImportada):
        await RascunhoService(mock_db).criar_rascunho(_XML_SIMPLES, tenant_id)


# ─── buscar ───────────────────────────────────────────────────────────────────

async def test_buscar_nao_encontrado_levanta_nao_encontrado(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()
    with pytest.raises(NaoEncontrado):
        await RascunhoService(mock_db).buscar(uuid.uuid4(), tenant_id)


async def test_buscar_retorna_rascunho(mock_db, tenant_id):
    r = _rascunho(tenant_id)
    mock_db.execute.return_value = resultado_com(r)
    resultado = await RascunhoService(mock_db).buscar(r.id, tenant_id)
    assert resultado.id == r.id


# ─── vincular_item ────────────────────────────────────────────────────────────

async def test_vincular_item_vincula_produto_existente(mock_db, tenant_id):
    r = _rascunho(tenant_id)
    item = _item_rascunho(r.id)
    produto = _produto(tenant_id)
    mock_db.execute.side_effect = [
        resultado_com(r),       # buscar rascunho
        resultado_com(item),    # buscar item
        resultado_com(produto), # verificar produto existe
    ]

    payload = VincularItemPayload(acao="vincular", produto_id=produto.id)
    resultado = await RascunhoService(mock_db).vincular_item(r.id, item.id, tenant_id, payload)

    assert resultado.produto_id == produto.id
    assert resultado.status_item == StatusItem.VINCULADO


async def test_vincular_item_cria_novo_produto(mock_db, tenant_id):
    r = _rascunho(tenant_id)
    item = _item_rascunho(r.id)
    mock_db.execute.side_effect = [
        resultado_com(r),    # buscar rascunho
        resultado_com(item), # buscar item
    ]

    payload = VincularItemPayload(acao="criar_novo")
    resultado = await RascunhoService(mock_db).vincular_item(r.id, item.id, tenant_id, payload)

    assert resultado.status_item == StatusItem.NOVO
    # produto_id is None in mock (flush doesn't set DB defaults), but Produto was added
    added_types = [type(call.args[0]).__name__ for call in mock_db.add.call_args_list]
    assert "Produto" in added_types


async def test_vincular_item_rascunho_ja_confirmado_levanta_erro(mock_db, tenant_id):
    r = _rascunho(tenant_id, status=StatusRascunho.CONFIRMADA)
    mock_db.execute.return_value = resultado_com(r)

    payload = VincularItemPayload(acao="vincular", produto_id=uuid.uuid4())
    with pytest.raises(RascunhoJaConfirmado):
        await RascunhoService(mock_db).vincular_item(r.id, uuid.uuid4(), tenant_id, payload)


async def test_vincular_item_nao_encontrado_levanta_erro(mock_db, tenant_id):
    r = _rascunho(tenant_id)
    mock_db.execute.side_effect = [
        resultado_com(r),    # buscar rascunho
        resultado_vazio(),   # item não encontrado
    ]

    payload = VincularItemPayload(acao="vincular", produto_id=uuid.uuid4())
    with pytest.raises(NaoEncontrado):
        await RascunhoService(mock_db).vincular_item(r.id, uuid.uuid4(), tenant_id, payload)


# ─── confirmar ────────────────────────────────────────────────────────────────

async def test_confirmar_com_itens_pendentes_levanta_rascunho_pendente(mock_db, tenant_id):
    r = _rascunho(tenant_id)
    item_pendente = _item_rascunho(r.id, status=StatusItem.PENDENTE)
    mock_db.execute.side_effect = [
        resultado_com(r),                   # buscar rascunho
        resultado_lista([item_pendente]),    # carregar itens
    ]

    with pytest.raises(RascunhoPendente):
        await RascunhoService(mock_db).confirmar(r.id, tenant_id)


async def test_confirmar_ja_confirmado_levanta_erro(mock_db, tenant_id):
    r = _rascunho(tenant_id, status=StatusRascunho.CONFIRMADA)
    mock_db.execute.return_value = resultado_com(r)

    with pytest.raises(RascunhoJaConfirmado):
        await RascunhoService(mock_db).confirmar(r.id, tenant_id)


async def test_confirmar_happy_path_cria_entrada_e_movimenta_estoque(mock_db, tenant_id):
    r = _rascunho(tenant_id)
    produto = _produto(tenant_id)
    item = _item_rascunho(r.id, status=StatusItem.VINCULADO)
    item.produto_id = produto.id

    mock_db.execute.side_effect = [
        resultado_com(r),           # buscar rascunho
        resultado_lista([item]),    # carregar itens
        resultado_com(produto),     # registrar_movimentacao — buscar produto
        resultado_vazio(),          # _upsert_mapeamento (pg_insert execute)
    ]

    with patch(
        "oficinas.modules.estoque.service.EstoqueService.registrar_movimentacao",
        new_callable=AsyncMock,
    ):
        entrada = await RascunhoService(mock_db).confirmar(r.id, tenant_id)

    assert r.status == StatusRascunho.CONFIRMADA
    mock_db.add.assert_called()
    mock_db.commit.assert_called()


# ─── cancelar ─────────────────────────────────────────────────────────────────

async def test_cancelar_muda_status_para_cancelada(mock_db, tenant_id):
    r = _rascunho(tenant_id)
    mock_db.execute.return_value = resultado_com(r)

    resultado = await RascunhoService(mock_db).cancelar(r.id, tenant_id)

    assert resultado.status == StatusRascunho.CANCELADA
    mock_db.commit.assert_called_once()


async def test_cancelar_rascunho_ja_confirmado_levanta_erro(mock_db, tenant_id):
    r = _rascunho(tenant_id, status=StatusRascunho.CONFIRMADA)
    mock_db.execute.return_value = resultado_com(r)

    with pytest.raises(RascunhoJaConfirmado):
        await RascunhoService(mock_db).cancelar(r.id, tenant_id)
