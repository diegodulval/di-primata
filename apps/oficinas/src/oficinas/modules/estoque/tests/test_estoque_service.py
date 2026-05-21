import uuid
from decimal import Decimal

import pytest

from oficinas.core.enums import TipoMovimentacao
from oficinas.core.exceptions import EstoqueInsuficiente, NaoEncontrado, NFeJaImportada
from oficinas.modules.estoque.models import EntradaNfe, MovimentacaoEstoque
from oficinas.modules.estoque.schemas import FornecedorCreate, ProdutoCreate, ProdutoUpdate
from oficinas.modules.estoque.service import EstoqueService
from oficinas.modules.estoque.tests.conftest import resultado_com, resultado_lista, resultado_vazio


# ─── Produto ──────────────────────────────────────────────────────────────────

async def test_criar_produto_persiste_com_estoque_zero(mock_db, tenant_id):
    p = await EstoqueService(mock_db).criar_produto(
        tenant_id,
        ProdutoCreate(codigo="P001", descricao="Filtro", preco_custo=Decimal("10")),
    )
    assert p.codigo == "P001"
    assert p.estoque_atual == Decimal("0")
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


async def test_buscar_produto_nao_encontrado_levanta_nao_encontrado(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()
    with pytest.raises(NaoEncontrado):
        await EstoqueService(mock_db).buscar_produto(uuid.uuid4(), tenant_id)


async def test_atualizar_produto_preco(mock_db, produto):
    mock_db.execute.return_value = resultado_com(produto)
    p = await EstoqueService(mock_db).atualizar_produto(
        produto.id, produto.tenant_id, ProdutoUpdate(preco_venda=Decimal("45.00"))
    )
    assert p.preco_venda == Decimal("45.00")
    mock_db.commit.assert_called_once()


async def test_atualizar_produto_ignora_campos_none(mock_db, produto):
    mock_db.execute.return_value = resultado_com(produto)
    codigo_original = produto.codigo
    await EstoqueService(mock_db).atualizar_produto(
        produto.id, produto.tenant_id, ProdutoUpdate(preco_venda=Decimal("99"))
    )
    assert produto.codigo == codigo_original


# ─── Movimentação ─────────────────────────────────────────────────────────────

async def test_registrar_entrada_aumenta_estoque(mock_db, produto):
    produto.estoque_atual = Decimal("5.000")
    mock_db.execute.return_value = resultado_com(produto)

    mov = await EstoqueService(mock_db).registrar_movimentacao(
        produto.id, produto.tenant_id,
        TipoMovimentacao.ENTRADA, Decimal("10"),
    )

    assert produto.estoque_atual == Decimal("15.000")
    assert mov.estoque_novo == Decimal("15.000")
    assert mov.tipo_mov == TipoMovimentacao.ENTRADA
    mock_db.add.assert_called_once_with(mov)


async def test_registrar_reserva_reduz_estoque(mock_db, produto):
    produto.estoque_atual = Decimal("5.000")
    mock_db.execute.return_value = resultado_com(produto)

    mov = await EstoqueService(mock_db).registrar_movimentacao(
        produto.id, produto.tenant_id,
        TipoMovimentacao.RESERVA, Decimal("3"),
    )

    assert produto.estoque_atual == Decimal("2.000")
    assert mov.estoque_anterior == Decimal("5.000")
    assert mov.estoque_novo == Decimal("2.000")


async def test_registrar_reserva_sem_saldo_levanta_estoque_insuficiente(mock_db, produto):
    produto.estoque_atual = Decimal("1.000")
    mock_db.execute.return_value = resultado_com(produto)

    with pytest.raises(EstoqueInsuficiente):
        await EstoqueService(mock_db).registrar_movimentacao(
            produto.id, produto.tenant_id,
            TipoMovimentacao.RESERVA, Decimal("5"),
        )
    mock_db.add.assert_not_called()


async def test_registrar_saida_nao_altera_estoque(mock_db, produto):
    """SAIDA é só registro contábil — estoque já foi reduzido pela RESERVA."""
    produto.estoque_atual = Decimal("2.000")
    mock_db.execute.return_value = resultado_com(produto)

    mov = await EstoqueService(mock_db).registrar_movimentacao(
        produto.id, produto.tenant_id,
        TipoMovimentacao.SAIDA, Decimal("3"),
    )

    assert produto.estoque_atual == Decimal("2.000")
    assert mov.estoque_anterior == Decimal("2.000")
    assert mov.estoque_novo == Decimal("2.000")


async def test_registrar_liberacao_devolve_estoque(mock_db, produto):
    produto.estoque_atual = Decimal("2.000")
    mock_db.execute.return_value = resultado_com(produto)

    mov = await EstoqueService(mock_db).registrar_movimentacao(
        produto.id, produto.tenant_id,
        TipoMovimentacao.LIBERACAO, Decimal("3"),
    )

    assert produto.estoque_atual == Decimal("5.000")
    assert mov.estoque_novo == Decimal("5.000")


async def test_registrar_movimentacao_com_referencia(mock_db, produto):
    ref_id = uuid.uuid4()
    mock_db.execute.return_value = resultado_com(produto)

    mov = await EstoqueService(mock_db).registrar_movimentacao(
        produto.id, produto.tenant_id,
        TipoMovimentacao.ENTRADA, Decimal("5"),
        referencia_id=ref_id, tipo_ref="ENTRADA",
    )

    assert mov.referencia_id == ref_id
    assert mov.tipo_ref == "ENTRADA"


async def test_registrar_movimentacao_nao_commita(mock_db, produto):
    """O commit é responsabilidade do chamador (composição transacional)."""
    mock_db.execute.return_value = resultado_com(produto)
    await EstoqueService(mock_db).registrar_movimentacao(
        produto.id, produto.tenant_id,
        TipoMovimentacao.ENTRADA, Decimal("1"),
    )
    mock_db.commit.assert_not_called()


# ─── NF-e ─────────────────────────────────────────────────────────────────────

async def test_processar_entrada_xml_cria_entrada(mock_db, tenant_id, xml_fixture, fornecedor, produto):
    """Happy path: fornecedor e produto já existem, sem duplicata de chave."""
    mock_db.execute.side_effect = [
        resultado_vazio(),          # chave_nfe check → não existe
        resultado_com(fornecedor),  # _upsert_fornecedor → encontrou
        resultado_com(produto),     # _upsert_produto → encontrou
        resultado_com(produto),     # registrar_movimentacao → buscar_produto
    ]

    entrada = await EstoqueService(mock_db).processar_entrada_xml(xml_fixture, tenant_id)

    assert entrada.chave_nfe == "35231212345678000195550010000001231000000001"
    assert entrada.numero_nf == "123"
    mock_db.commit.assert_called_once()


async def test_processar_entrada_xml_chave_duplicada_levanta_nfe_ja_importada(
    mock_db, tenant_id, xml_fixture, fornecedor
):
    entrada_existente = EntradaNfe(
        id=uuid.uuid4(), tenant_id=tenant_id,
        chave_nfe="35231212345678000195550010000001231000000001",
    )
    mock_db.execute.return_value = resultado_com(entrada_existente)

    with pytest.raises(NFeJaImportada):
        await EstoqueService(mock_db).processar_entrada_xml(xml_fixture, tenant_id)
    mock_db.commit.assert_not_called()


async def test_processar_entrada_xml_invalido_levanta_value_error(mock_db, tenant_id):
    with pytest.raises(ValueError):
        await EstoqueService(mock_db).processar_entrada_xml(b"xml invalido", tenant_id)


async def test_processar_entrada_xml_cria_fornecedor_se_nao_existir(
    mock_db, tenant_id, xml_fixture, produto
):
    mock_db.execute.side_effect = [
        resultado_vazio(),  # chave_nfe → não existe
        resultado_vazio(),  # fornecedor por CNPJ → não existe (vai criar)
        resultado_com(produto),  # _upsert_produto → encontrou
        resultado_com(produto),  # registrar_movimentacao
    ]

    await EstoqueService(mock_db).processar_entrada_xml(xml_fixture, tenant_id)

    # add foi chamado ao menos para fornecedor + entrada + item + movimentacao
    assert mock_db.add.call_count >= 3
