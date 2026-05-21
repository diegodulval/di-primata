import uuid
from datetime import date, datetime, timezone

import pytest

from oficinas.core.exceptions import NaoEncontrado
from oficinas.modules.cadastros.models import Cliente, ClienteVeiculo
from oficinas.modules.cadastros.schemas import ClienteCreate, ClienteUpdate, ClienteVeiculoCreate
from oficinas.modules.cadastros.service import CadastroService
from oficinas.modules.cadastros.tests.conftest import resultado_com, resultado_lista, resultado_vazio


# ─── Criar cliente ────────────────────────────────────────────────────────────

async def test_criar_cliente_persiste_e_retorna(mock_db, tenant_id):
    payload = ClienteCreate(nome="Maria Costa", telefone="11988880000")

    cliente = await CadastroService(mock_db).criar_cliente(tenant_id, payload)

    assert cliente.nome == "Maria Costa"
    assert cliente.telefone == "11988880000"
    assert cliente.tenant_id == tenant_id
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


async def test_criar_cliente_campos_opcionais_nulos(mock_db, tenant_id):
    payload = ClienteCreate(nome="Apenas Nome")

    cliente = await CadastroService(mock_db).criar_cliente(tenant_id, payload)

    assert cliente.cpf_cnpj is None
    assert cliente.email is None


# ─── Buscar e listar ──────────────────────────────────────────────────────────

async def test_buscar_cliente_encontrado(mock_db, cliente):
    mock_db.execute.return_value = resultado_com(cliente)

    resultado = await CadastroService(mock_db).buscar_cliente(cliente.id, cliente.tenant_id)

    assert resultado.nome == "João Silva"


async def test_buscar_cliente_nao_encontrado_levanta_nao_encontrado(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()

    with pytest.raises(NaoEncontrado):
        await CadastroService(mock_db).buscar_cliente(uuid.uuid4(), tenant_id)


async def test_listar_clientes_retorna_todos(mock_db, tenant_id, cliente):
    mock_db.execute.return_value = resultado_lista([cliente])

    items = await CadastroService(mock_db).listar_clientes(tenant_id)

    assert len(items) == 1
    assert items[0].nome == "João Silva"


async def test_buscar_por_q_delega_query_correta(mock_db, tenant_id, cliente):
    mock_db.execute.return_value = resultado_lista([cliente])

    items = await CadastroService(mock_db).buscar_por_q("joão", tenant_id)

    assert len(items) == 1
    mock_db.execute.assert_called_once()


# ─── Atualizar ────────────────────────────────────────────────────────────────

async def test_atualizar_cliente_nome(mock_db, cliente):
    mock_db.execute.return_value = resultado_com(cliente)

    resultado = await CadastroService(mock_db).atualizar_cliente(
        cliente.id, cliente.tenant_id, ClienteUpdate(nome="João Atualizado")
    )

    assert resultado.nome == "João Atualizado"
    mock_db.commit.assert_called_once()


async def test_atualizar_cliente_ignora_campos_none(mock_db, cliente):
    mock_db.execute.return_value = resultado_com(cliente)
    telefone_original = cliente.telefone

    await CadastroService(mock_db).atualizar_cliente(
        cliente.id, cliente.tenant_id, ClienteUpdate(nome="Novo Nome")
    )

    assert cliente.telefone == telefone_original  # não foi sobrescrito


# ─── Vínculo cliente-veículo ──────────────────────────────────────────────────

async def test_vincular_veiculo_sem_link_anterior(mock_db, cliente, veiculo_id):
    # buscar_cliente → cliente; buscar link ativo → None
    mock_db.execute.side_effect = [resultado_com(cliente), resultado_vazio()]

    link = await CadastroService(mock_db).vincular_veiculo(
        cliente.id, veiculo_id, cliente.tenant_id
    )

    assert link.cliente_id == cliente.id
    assert link.veiculo_id == veiculo_id
    assert link.ativo is True
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


async def test_vincular_veiculo_idempotente_mesmo_cliente(mock_db, cliente, link_ativo):
    mock_db.execute.side_effect = [resultado_com(cliente), resultado_com(link_ativo)]

    resultado = await CadastroService(mock_db).vincular_veiculo(
        cliente.id, link_ativo.veiculo_id, cliente.tenant_id
    )

    assert resultado is link_ativo  # retornou o link existente sem criar outro
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


async def test_vincular_veiculo_troca_dono_fecha_link_anterior(mock_db, tenant_id, veiculo_id):
    dono_antigo_id = uuid.uuid4()
    novo_dono_id = uuid.uuid4()

    dono_antigo = Cliente(
        id=dono_antigo_id, tenant_id=tenant_id, nome="Dono Antigo",
        criado_em=datetime.now(timezone.utc),
    )
    novo_dono = Cliente(
        id=novo_dono_id, tenant_id=tenant_id, nome="Novo Dono",
        criado_em=datetime.now(timezone.utc),
    )
    link_anterior = ClienteVeiculo(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        cliente_id=dono_antigo_id,
        veiculo_id=veiculo_id,
        data_inicio=date(2023, 1, 1),
        data_fim=None,
        ativo=True,
    )

    mock_db.execute.side_effect = [resultado_com(novo_dono), resultado_com(link_anterior)]

    await CadastroService(mock_db).vincular_veiculo(novo_dono_id, veiculo_id, tenant_id)

    assert link_anterior.ativo is False
    assert link_anterior.data_fim == date.today()
    mock_db.add.assert_called_once()  # novo link criado
    mock_db.commit.assert_called_once()


# ─── Listar veículos do cliente ───────────────────────────────────────────────

async def test_listar_veiculos_cliente(mock_db, cliente, link_ativo):
    mock_db.execute.side_effect = [resultado_com(cliente), resultado_lista([link_ativo])]

    items = await CadastroService(mock_db).listar_veiculos_cliente(
        cliente.id, cliente.tenant_id
    )

    assert len(items) == 1
    assert items[0].veiculo_id == link_ativo.veiculo_id


# ─── Desassociar veículo ──────────────────────────────────────────────────────

async def test_desassociar_veiculo_fecha_link(mock_db, cliente, link_ativo, veiculo_id):
    mock_db.execute.return_value = resultado_com(link_ativo)

    resultado = await CadastroService(mock_db).desassociar_veiculo(
        cliente.id, veiculo_id, cliente.tenant_id
    )

    assert resultado.ativo is False
    assert resultado.data_fim == date.today()
    mock_db.commit.assert_called_once()


async def test_desassociar_veiculo_sem_link_ativo_levanta_nao_encontrado(mock_db, cliente, veiculo_id):
    mock_db.execute.return_value = resultado_vazio()

    with pytest.raises(NaoEncontrado):
        await CadastroService(mock_db).desassociar_veiculo(
            cliente.id, veiculo_id, cliente.tenant_id
        )
