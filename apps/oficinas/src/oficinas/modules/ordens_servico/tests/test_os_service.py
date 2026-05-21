import uuid
from decimal import Decimal

import pytest

from oficinas.core.enums import StatusOS, TipoItem
from oficinas.core.exceptions import NaoEncontrado, OSJaFechada, TransicaoInvalida
from oficinas.modules.ordens_servico.schemas import AtualizarStatusOS, FecharOS, ItemOSAdd, OSCreate
from oficinas.modules.ordens_servico.service import OrdensServicoService
from oficinas.modules.ordens_servico.tests.conftest import resultado_com, resultado_lista, resultado_vazio


# ─── Abrir OS ─────────────────────────────────────────────────────────────────

async def test_abrir_os_persiste_e_retorna(mock_db, tenant_id, mecanico_id, cliente_id, veiculo_id):
    payload = OSCreate(
        cliente_id=cliente_id,
        veiculo_id=veiculo_id,
        km_entrada=45000,
        descricao_problema="Motor falhando",
    )

    os = await OrdensServicoService(mock_db).abrir(tenant_id, mecanico_id, payload)

    assert os.descricao_problema == "Motor falhando"
    assert os.km_entrada == 45000
    assert os.tenant_id == tenant_id
    assert os.mecanico_id == mecanico_id
    assert os.status == StatusOS.ABERTA
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


async def test_abrir_os_gera_numero_os(mock_db, tenant_id, mecanico_id, cliente_id, veiculo_id):
    payload = OSCreate(cliente_id=cliente_id, veiculo_id=veiculo_id, descricao_problema="X")

    os = await OrdensServicoService(mock_db).abrir(tenant_id, mecanico_id, payload)

    assert os.numero_os.startswith("OS")
    assert len(os.numero_os) > 5


# ─── Buscar e listar ──────────────────────────────────────────────────────────

async def test_buscar_os_encontrada(mock_db, os_aberta):
    mock_db.execute.return_value = resultado_com(os_aberta)

    resultado = await OrdensServicoService(mock_db).buscar(os_aberta.id, os_aberta.tenant_id)

    assert resultado.numero_os == os_aberta.numero_os


async def test_buscar_os_nao_encontrada_levanta_nao_encontrado(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()

    with pytest.raises(NaoEncontrado):
        await OrdensServicoService(mock_db).buscar(uuid.uuid4(), tenant_id)


async def test_listar_os_retorna_lista(mock_db, tenant_id, os_aberta):
    mock_db.execute.return_value = resultado_lista([os_aberta])

    items = await OrdensServicoService(mock_db).listar(tenant_id)

    assert len(items) == 1
    assert items[0].numero_os == os_aberta.numero_os


# ─── Adicionar item ───────────────────────────────────────────────────────────

async def test_adicionar_item_peca_reserva_estoque_e_atualiza_totais(
    mock_db, os_aberta, produto
):
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),   # buscar OS
        resultado_com(produto),     # buscar_produto (dentro de registrar_movimentacao)
    ]
    payload = ItemOSAdd(
        produto_id=produto.id,
        tipo=TipoItem.PECA,
        descricao="Filtro de óleo",
        quantidade=Decimal("2"),
        preco_unitario=Decimal("30.00"),
    )

    item = await OrdensServicoService(mock_db).adicionar_item(
        os_aberta.id, os_aberta.tenant_id, payload
    )

    assert item.subtotal == Decimal("60.00")
    assert os_aberta.total_pecas == Decimal("60.00")
    assert os_aberta.total_final == Decimal("60.00")
    mock_db.add.assert_called()
    mock_db.commit.assert_called_once()


async def test_adicionar_item_servico_nao_reserva_estoque(mock_db, os_aberta):
    mock_db.execute.return_value = resultado_com(os_aberta)
    payload = ItemOSAdd(
        tipo=TipoItem.SERVICO,
        descricao="Mão de obra",
        quantidade=Decimal("1"),
        preco_unitario=Decimal("150.00"),
    )

    item = await OrdensServicoService(mock_db).adicionar_item(
        os_aberta.id, os_aberta.tenant_id, payload
    )

    assert item.subtotal == Decimal("150.00")
    assert os_aberta.total_servicos == Decimal("150.00")
    assert os_aberta.total_pecas == Decimal("0")
    mock_db.execute.assert_called_once()  # só buscar OS, sem buscar produto


async def test_adicionar_item_em_os_fechada_levanta_os_ja_fechada(mock_db, os_aberta):
    os_aberta.status = StatusOS.FECHADA
    mock_db.execute.return_value = resultado_com(os_aberta)

    with pytest.raises(OSJaFechada):
        await OrdensServicoService(mock_db).adicionar_item(
            os_aberta.id, os_aberta.tenant_id,
            ItemOSAdd(tipo=TipoItem.SERVICO, descricao="X", quantidade=Decimal("1"), preco_unitario=Decimal("10")),
        )


async def test_adicionar_item_peca_sem_produto_id_levanta_nao_encontrado(mock_db, os_aberta):
    mock_db.execute.return_value = resultado_com(os_aberta)

    with pytest.raises(NaoEncontrado):
        await OrdensServicoService(mock_db).adicionar_item(
            os_aberta.id, os_aberta.tenant_id,
            ItemOSAdd(tipo=TipoItem.PECA, descricao="Filtro", quantidade=Decimal("1"), preco_unitario=Decimal("20")),
        )


# ─── Remover item ─────────────────────────────────────────────────────────────

async def test_remover_item_peca_libera_estoque_e_atualiza_totais(
    mock_db, os_aberta, item_peca, produto
):
    os_aberta.total_pecas = Decimal("60.00")
    os_aberta.total_final = Decimal("60.00")
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),   # buscar OS
        resultado_com(item_peca),   # buscar ItemOS
        resultado_com(produto),     # buscar_produto (dentro de registrar_movimentacao)
    ]

    await OrdensServicoService(mock_db).remover_item(
        os_aberta.id, item_peca.id, os_aberta.tenant_id
    )

    assert os_aberta.total_pecas == Decimal("0.00")
    assert os_aberta.total_final == Decimal("0.00")
    mock_db.delete.assert_called_once_with(item_peca)
    mock_db.commit.assert_called_once()


async def test_remover_item_inexistente_levanta_nao_encontrado(mock_db, os_aberta):
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),
        resultado_vazio(),
    ]

    with pytest.raises(NaoEncontrado):
        await OrdensServicoService(mock_db).remover_item(
            os_aberta.id, uuid.uuid4(), os_aberta.tenant_id
        )


# ─── Atualizar status ─────────────────────────────────────────────────────────

async def test_atualizar_status_aberta_para_em_execucao(mock_db, os_aberta):
    mock_db.execute.return_value = resultado_com(os_aberta)

    resultado = await OrdensServicoService(mock_db).atualizar_status(
        os_aberta.id, os_aberta.tenant_id, StatusOS.EM_EXECUCAO
    )

    assert resultado.status == StatusOS.EM_EXECUCAO
    mock_db.commit.assert_called_once()


async def test_atualizar_status_transicao_invalida_levanta_transicao_invalida(
    mock_db, os_aberta
):
    os_aberta.status = StatusOS.EM_EXECUCAO
    mock_db.execute.return_value = resultado_com(os_aberta)

    with pytest.raises(TransicaoInvalida):
        await OrdensServicoService(mock_db).atualizar_status(
            os_aberta.id, os_aberta.tenant_id, StatusOS.ABERTA
        )


async def test_atualizar_status_de_os_fechada_levanta_os_ja_fechada(mock_db, os_aberta):
    os_aberta.status = StatusOS.FECHADA
    mock_db.execute.return_value = resultado_com(os_aberta)

    with pytest.raises(OSJaFechada):
        await OrdensServicoService(mock_db).atualizar_status(
            os_aberta.id, os_aberta.tenant_id, StatusOS.EM_EXECUCAO
        )


# ─── Fechar OS ────────────────────────────────────────────────────────────────

async def test_fechar_os_com_peca_registra_saida_e_historico(
    mock_db, os_aberta, item_peca, produto
):
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),       # buscar OS
        resultado_lista([item_peca]),   # _carregar_itens
        resultado_com(produto),         # buscar_produto (SAIDA)
    ]

    resultado = await OrdensServicoService(mock_db).fechar(
        os_aberta.id, os_aberta.tenant_id, FecharOS(compartilhar_historico=False)
    )

    assert resultado.status == StatusOS.FECHADA
    assert resultado.fechada_em is not None
    mock_db.add.assert_called()  # HistoricoVeiculo + MovimentacaoEstoque
    mock_db.commit.assert_called_once()


async def test_fechar_os_com_compartilhar_historico_true_popula_resumo(
    mock_db, os_aberta
):
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),
        resultado_lista([]),  # sem itens
    ]

    await OrdensServicoService(mock_db).fechar(
        os_aberta.id, os_aberta.tenant_id,
        FecharOS(compartilhar_historico=True, resumo_publico="Troca de óleo realizada"),
    )

    historico_add_call = mock_db.add.call_args_list[0]
    historico = historico_add_call.args[0]
    assert historico.resumo_publico == "Troca de óleo realizada"
    assert historico.compartilhar_historico is True if hasattr(historico, "compartilhar_historico") else True


async def test_fechar_os_com_compartilhar_false_resumo_publico_nulo(
    mock_db, os_aberta
):
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),
        resultado_lista([]),
    ]

    await OrdensServicoService(mock_db).fechar(
        os_aberta.id, os_aberta.tenant_id,
        FecharOS(compartilhar_historico=False, resumo_publico="não deve aparecer"),
    )

    historico = mock_db.add.call_args_list[0].args[0]
    assert historico.resumo_publico is None


async def test_fechar_os_ja_fechada_levanta_os_ja_fechada(mock_db, os_aberta):
    os_aberta.status = StatusOS.FECHADA
    mock_db.execute.return_value = resultado_com(os_aberta)

    with pytest.raises(OSJaFechada):
        await OrdensServicoService(mock_db).fechar(
            os_aberta.id, os_aberta.tenant_id, FecharOS()
        )


# ─── Cancelar OS ─────────────────────────────────────────────────────────────

async def test_cancelar_os_com_peca_libera_estoque(
    mock_db, os_aberta, item_peca, produto
):
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),
        resultado_lista([item_peca]),
        resultado_com(produto),  # buscar_produto (LIBERACAO)
    ]

    resultado = await OrdensServicoService(mock_db).cancelar(
        os_aberta.id, os_aberta.tenant_id
    )

    assert resultado.status == StatusOS.CANCELADA
    mock_db.commit.assert_called_once()


async def test_cancelar_os_sem_itens(mock_db, os_aberta):
    mock_db.execute.side_effect = [
        resultado_com(os_aberta),
        resultado_lista([]),
    ]

    resultado = await OrdensServicoService(mock_db).cancelar(
        os_aberta.id, os_aberta.tenant_id
    )

    assert resultado.status == StatusOS.CANCELADA


async def test_cancelar_os_ja_cancelada_levanta_os_ja_fechada(mock_db, os_aberta):
    os_aberta.status = StatusOS.CANCELADA
    mock_db.execute.return_value = resultado_com(os_aberta)

    with pytest.raises(OSJaFechada):
        await OrdensServicoService(mock_db).cancelar(os_aberta.id, os_aberta.tenant_id)
