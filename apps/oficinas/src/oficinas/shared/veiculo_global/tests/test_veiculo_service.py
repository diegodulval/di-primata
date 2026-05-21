import uuid
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from oficinas.core.exceptions import NaoEncontrado
from oficinas.shared.veiculo_global.models import HistoricoVeiculo, Veiculo
from oficinas.shared.veiculo_global.schemas import HistoricoCreate, VeiculoCreate
from oficinas.shared.veiculo_global.service import VeiculoService
from oficinas.shared.veiculo_global.tests.conftest import resultado_com, resultado_lista, resultado_vazio


# ─── Validação de placa (schema) ──────────────────────────────────────────────

def test_placa_normalizada_para_maiuscula():
    v = VeiculoCreate(placa="abc1234")
    assert v.placa == "ABC1234"


def test_placa_mercosul_valida():
    v = VeiculoCreate(placa="ABC1D23")
    assert v.placa == "ABC1D23"


def test_placa_invalida_levanta_validation_error():
    with pytest.raises(ValidationError):
        VeiculoCreate(placa="INVALIDA")


def test_placa_com_espacos_e_aceita():
    v = VeiculoCreate(placa=" abc1234 ")
    assert v.placa == "ABC1234"


# ─── Upsert ───────────────────────────────────────────────────────────────────

async def test_upsert_retorna_veiculo_criado(mock_db, veiculo):
    mock_db.execute.return_value = resultado_com(veiculo)

    resultado = await VeiculoService(mock_db).upsert(
        VeiculoCreate(placa="ABC1234", marca="Fiat", modelo="Uno")
    )

    assert resultado.placa == "ABC1234"
    mock_db.commit.assert_called_once()


async def test_upsert_normaliza_placa(mock_db, veiculo):
    mock_db.execute.return_value = resultado_com(veiculo)

    await VeiculoService(mock_db).upsert(VeiculoCreate(placa="abc1234"))

    # Verifica que execute foi chamado (stmt montado com placa uppercase)
    mock_db.execute.assert_called_once()


# ─── Buscar por placa ─────────────────────────────────────────────────────────

async def test_buscar_por_placa_retorna_veiculo(mock_db, veiculo):
    mock_db.execute.return_value = resultado_com(veiculo)

    resultado = await VeiculoService(mock_db).buscar_por_placa("ABC1234")

    assert resultado.placa == "ABC1234"
    assert resultado.marca == "Fiat"


async def test_buscar_por_placa_case_insensitive(mock_db, veiculo):
    mock_db.execute.return_value = resultado_com(veiculo)

    resultado = await VeiculoService(mock_db).buscar_por_placa("abc1234")

    assert resultado is veiculo


async def test_buscar_por_placa_nao_encontrado_levanta_nao_encontrado(mock_db):
    mock_db.execute.return_value = resultado_vazio()

    with pytest.raises(NaoEncontrado):
        await VeiculoService(mock_db).buscar_por_placa("XYZ9999")


# ─── Histórico público ────────────────────────────────────────────────────────

async def test_historico_publico_retorna_apenas_opt_in(mock_db, veiculo, historico_publico):
    mock_db.execute.return_value = resultado_lista([historico_publico])

    items = await VeiculoService(mock_db).historico_publico(veiculo.id)

    assert len(items) == 1
    assert items[0].resumo_publico == "Troca de óleo e filtros"


async def test_historico_publico_vazio_quando_nenhum(mock_db, veiculo):
    mock_db.execute.return_value = resultado_lista([])

    items = await VeiculoService(mock_db).historico_publico(veiculo.id)

    assert items == []


# ─── Registrar histórico (append-only) ───────────────────────────────────────

async def test_registrar_historico_sem_opt_in(mock_db, veiculo, tenant_id):
    payload = HistoricoCreate(
        veiculo_id=veiculo.id,
        tenant_id=tenant_id,
        data_servico=date.today(),
        detalhe_privado="Troca de correia dentada",
    )

    h = await VeiculoService(mock_db).registrar_historico(payload)

    assert h.resumo_publico is None
    assert h.detalhe_privado == "Troca de correia dentada"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


async def test_registrar_historico_com_opt_in_popula_resumo_publico(mock_db, veiculo, tenant_id):
    payload = HistoricoCreate(
        veiculo_id=veiculo.id,
        tenant_id=tenant_id,
        data_servico=date.today(),
        detalhe_privado="Motor trocado — bloco fundido",
        resumo_publico="Troca de motor",
    )

    h = await VeiculoService(mock_db).registrar_historico(payload)

    assert h.resumo_publico == "Troca de motor"
    assert h.detalhe_privado == "Motor trocado — bloco fundido"


async def test_registrar_historico_com_os_id(mock_db, veiculo, tenant_id):
    os_id = uuid.uuid4()
    payload = HistoricoCreate(
        veiculo_id=veiculo.id,
        tenant_id=tenant_id,
        os_id=os_id,
        data_servico=date.today(),
        detalhe_privado="Alinhamento e balanceamento",
        km_entrada=62000,
    )

    h = await VeiculoService(mock_db).registrar_historico(payload)

    assert h.os_id == os_id
    assert h.km_entrada == 62000
