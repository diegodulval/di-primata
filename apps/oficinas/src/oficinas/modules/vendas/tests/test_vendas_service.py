import uuid
from decimal import Decimal

import pytest

from oficinas.core.enums import OrigemVenda, TipoMovimentacao
from oficinas.core.exceptions import EstoqueInsuficiente, NaoEncontrado
from oficinas.modules.vendas.schemas import ItemVendaIn, VendaCreate
from oficinas.modules.vendas.service import VendasService
from oficinas.modules.vendas.tests.conftest import resultado_com, resultado_lista, resultado_vazio


# ─── Criar venda ──────────────────────────────────────────────────────────────

async def test_criar_venda_calcula_total_e_persiste(mock_db, tenant_id, produto):
    mock_db.execute.side_effect = [
        resultado_com(produto),  # RESERVA: buscar_produto
        resultado_com(produto),  # SAIDA: buscar_produto
    ]
    payload = VendaCreate(itens=[
        ItemVendaIn(produto_id=produto.id, quantidade=Decimal("2"), preco_unitario=Decimal("50"))
    ])

    venda = await VendasService(mock_db).criar(tenant_id, uuid.uuid4(), payload)

    assert venda.total == Decimal("100")
    assert venda.origem == OrigemVenda.BALCAO
    assert venda.status == "CONCLUIDA"
    assert venda.tenant_id == tenant_id
    mock_db.flush.assert_called_once()
    mock_db.commit.assert_called_once()
    # venda + item_venda + movimentacao_reserva + movimentacao_saida
    assert mock_db.add.call_count == 4


async def test_criar_venda_gera_numero_prefixado(mock_db, tenant_id, produto):
    mock_db.execute.side_effect = [resultado_com(produto), resultado_com(produto)]
    payload = VendaCreate(itens=[
        ItemVendaIn(produto_id=produto.id, quantidade=Decimal("1"), preco_unitario=Decimal("10"))
    ])

    venda = await VendasService(mock_db).criar(tenant_id, uuid.uuid4(), payload)

    assert venda.numero_venda.startswith("VDA")
    assert len(venda.numero_venda) > 8


async def test_criar_venda_sem_cliente_permitido(mock_db, tenant_id, produto):
    mock_db.execute.side_effect = [resultado_com(produto), resultado_com(produto)]
    payload = VendaCreate(
        cliente_id=None,
        itens=[ItemVendaIn(produto_id=produto.id, quantidade=Decimal("1"), preco_unitario=Decimal("10"))],
    )

    venda = await VendasService(mock_db).criar(tenant_id, uuid.uuid4(), payload)

    assert venda.cliente_id is None


async def test_criar_venda_multiplos_itens_soma_total(mock_db, tenant_id, produto):
    produto2_id = uuid.uuid4()
    from oficinas.modules.estoque.models import Produto as ProdutoModel
    produto2 = ProdutoModel(
        id=produto2_id,
        tenant_id=tenant_id,
        codigo="P002",
        descricao="Vela de ignição",
        ncm=None, marca=None, localizacao=None, ean=None,
        preco_custo=Decimal("5"), preco_venda=Decimal("10"),
        estoque_atual=Decimal("10"), estoque_minimo=Decimal("0"), estoque_maximo=Decimal("0"),
        ativo=True,
    )
    mock_db.execute.side_effect = [
        resultado_com(produto),   # RESERVA item 1
        resultado_com(produto),   # SAIDA item 1
        resultado_com(produto2),  # RESERVA item 2
        resultado_com(produto2),  # SAIDA item 2
    ]
    payload = VendaCreate(itens=[
        ItemVendaIn(produto_id=produto.id,  quantidade=Decimal("2"), preco_unitario=Decimal("50")),
        ItemVendaIn(produto_id=produto2_id, quantidade=Decimal("4"), preco_unitario=Decimal("10")),
    ])

    venda = await VendasService(mock_db).criar(tenant_id, uuid.uuid4(), payload)

    assert venda.total == Decimal("140")  # 100 + 40
    assert mock_db.add.call_count == 7    # venda + 2 itens + 4 movimentacoes


async def test_criar_venda_estoque_insuficiente_levanta_excecao(mock_db, tenant_id, produto):
    produto.estoque_atual = Decimal("0")
    mock_db.execute.side_effect = [resultado_com(produto)]
    payload = VendaCreate(itens=[
        ItemVendaIn(produto_id=produto.id, quantidade=Decimal("1"), preco_unitario=Decimal("10"))
    ])

    with pytest.raises(EstoqueInsuficiente):
        await VendasService(mock_db).criar(tenant_id, uuid.uuid4(), payload)


async def test_criar_venda_registra_movimentacoes_reserva_e_saida(mock_db, tenant_id, produto):
    mock_db.execute.side_effect = [resultado_com(produto), resultado_com(produto)]
    payload = VendaCreate(itens=[
        ItemVendaIn(produto_id=produto.id, quantidade=Decimal("1"), preco_unitario=Decimal("30"))
    ])

    await VendasService(mock_db).criar(tenant_id, uuid.uuid4(), payload)

    calls = mock_db.add.call_args_list
    from oficinas.modules.estoque.models import MovimentacaoEstoque
    movimentacoes = [c.args[0] for c in calls if isinstance(c.args[0], MovimentacaoEstoque)]
    tipos = {m.tipo_mov for m in movimentacoes}
    assert TipoMovimentacao.RESERVA in tipos
    assert TipoMovimentacao.SAIDA in tipos


# ─── Buscar ───────────────────────────────────────────────────────────────────

async def test_buscar_venda_retorna_venda(mock_db, venda):
    mock_db.execute.return_value = resultado_com(venda)

    resultado = await VendasService(mock_db).buscar(venda.id, venda.tenant_id)

    assert resultado.numero_venda == venda.numero_venda


async def test_buscar_venda_nao_encontrada_levanta_excecao(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()

    with pytest.raises(NaoEncontrado):
        await VendasService(mock_db).buscar(uuid.uuid4(), tenant_id)


# ─── Listar ───────────────────────────────────────────────────────────────────

async def test_listar_vendas_retorna_lista(mock_db, tenant_id, venda):
    mock_db.execute.return_value = resultado_lista([venda])

    resultados = await VendasService(mock_db).listar(tenant_id)

    assert len(resultados) == 1
    assert resultados[0].numero_venda == venda.numero_venda


async def test_listar_vendas_vazio(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_lista([])

    resultados = await VendasService(mock_db).listar(tenant_id)

    assert resultados == []


# ─── Listar itens ─────────────────────────────────────────────────────────────

async def test_listar_itens_retorna_itens(mock_db, venda, item_venda):
    mock_db.execute.return_value = resultado_lista([item_venda])

    itens = await VendasService(mock_db).listar_itens(venda.id)

    assert len(itens) == 1
    assert itens[0].subtotal == Decimal("100.00")
