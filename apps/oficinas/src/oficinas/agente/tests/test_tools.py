import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oficinas.agente.tools import executar_tool


def _parse(result: str) -> dict | list:
    return json.loads(result)


# ── buscar_veiculo ────────────────────────────────────────────────────────────

async def test_buscar_veiculo_encontrado(mock_db, mock_usuario):
    veiculo = MagicMock()
    veiculo.id = uuid.uuid4()
    veiculo.placa = "ABC1234"
    veiculo.marca = "Volkswagen"
    veiculo.modelo = "Gol"
    veiculo.cor = "prata"
    veiculo.tipo = "carro"
    veiculo.ano_fab = 2010
    veiculo.ano_mod = 2011

    with patch("oficinas.agente.tools.VeiculoService") as MockVS:
        MockVS.return_value.buscar_por_placa = AsyncMock(return_value=veiculo)
        result = await executar_tool("buscar_veiculo", {"placa": "ABC1234"}, mock_db, mock_usuario)

    data = _parse(result)
    assert data["placa"] == "ABC1234"
    assert data["marca"] == "Volkswagen"
    assert "id" in data


async def test_buscar_veiculo_nao_encontrado(mock_db, mock_usuario):
    with patch("oficinas.agente.tools.VeiculoService") as MockVS:
        MockVS.return_value.buscar_por_placa = AsyncMock(side_effect=Exception("não encontrado"))
        result = await executar_tool("buscar_veiculo", {"placa": "XYZ9999"}, mock_db, mock_usuario)

    assert "erro" in _parse(result)


# ── criar_veiculo ─────────────────────────────────────────────────────────────

async def test_criar_veiculo_sucesso(mock_db, mock_usuario):
    veiculo = MagicMock()
    veiculo.id = uuid.uuid4()
    veiculo.placa = "ABC1234"
    veiculo.marca = "Fiat"
    veiculo.modelo = "Uno"
    veiculo.cor = "branco"
    veiculo.tipo = "carro"

    with patch("oficinas.agente.tools.VeiculoService") as MockVS:
        MockVS.return_value.upsert = AsyncMock(return_value=veiculo)
        result = await executar_tool(
            "criar_veiculo",
            {"placa": "ABC1234", "marca": "Fiat", "modelo": "Uno", "cor": "branco", "tipo": "carro"},
            mock_db,
            mock_usuario,
        )

    data = _parse(result)
    assert data["placa"] == "ABC1234"
    assert "id" in data


async def test_criar_veiculo_erro(mock_db, mock_usuario):
    with patch("oficinas.agente.tools.VeiculoService") as MockVS:
        MockVS.return_value.upsert = AsyncMock(side_effect=Exception("falha no banco"))
        result = await executar_tool("criar_veiculo", {"placa": "ABC1234"}, mock_db, mock_usuario)

    assert "erro" in _parse(result)


# ── buscar_cliente ────────────────────────────────────────────────────────────

async def test_buscar_cliente_encontrado(mock_db, mock_usuario):
    cliente = MagicMock()
    cliente.id = uuid.uuid4()
    cliente.nome = "João Silva"
    cliente.telefone = "11999999999"
    cliente.cpf_cnpj = "12345678901"

    with patch("oficinas.agente.tools.CadastroService") as MockCS:
        MockCS.return_value.buscar_por_q = AsyncMock(return_value=[cliente])
        result = await executar_tool("buscar_cliente", {"q": "João"}, mock_db, mock_usuario)

    data = _parse(result)
    assert isinstance(data, list)
    assert data[0]["nome"] == "João Silva"


async def test_buscar_cliente_sem_resultado(mock_db, mock_usuario):
    with patch("oficinas.agente.tools.CadastroService") as MockCS:
        MockCS.return_value.buscar_por_q = AsyncMock(return_value=[])
        result = await executar_tool("buscar_cliente", {"q": "ninguem"}, mock_db, mock_usuario)

    assert _parse(result) == []


# ── abrir_os ──────────────────────────────────────────────────────────────────

async def test_abrir_os_sucesso(mock_db, mock_usuario):
    os = MagicMock()
    os.id = uuid.uuid4()
    os.numero_os = "OS202506-ABCDEF"
    os.status = "ABERTA"
    os.aberta_em = datetime.now(timezone.utc)

    with patch("oficinas.agente.tools.OrdensServicoService") as MockOS:
        MockOS.return_value.abrir = AsyncMock(return_value=os)
        result = await executar_tool(
            "abrir_os",
            {
                "cliente_id": str(uuid.uuid4()),
                "veiculo_id": str(uuid.uuid4()),
                "descricao_problema": "troca de óleo",
            },
            mock_db,
            mock_usuario,
        )

    data = _parse(result)
    assert data["numero_os"] == "OS202506-ABCDEF"
    assert data["status"] == "ABERTA"


async def test_abrir_os_erro(mock_db, mock_usuario):
    with patch("oficinas.agente.tools.OrdensServicoService") as MockOS:
        MockOS.return_value.abrir = AsyncMock(side_effect=Exception("cliente não encontrado"))
        result = await executar_tool(
            "abrir_os",
            {
                "cliente_id": str(uuid.uuid4()),
                "veiculo_id": str(uuid.uuid4()),
                "descricao_problema": "problema",
            },
            mock_db,
            mock_usuario,
        )

    assert "erro" in _parse(result)


# ── minhas_os ─────────────────────────────────────────────────────────────────

async def test_minhas_os_lista(mock_db, mock_usuario):
    os1 = MagicMock()
    os1.id = uuid.uuid4()
    os1.numero_os = "OS202506-000001"
    os1.status = "ABERTA"
    os1.descricao_problema = "troca de óleo"
    os1.aberta_em = datetime.now(timezone.utc)

    with patch("oficinas.agente.tools.OrdensServicoService") as MockOS:
        MockOS.return_value.listar = AsyncMock(return_value=[os1])
        result = await executar_tool("minhas_os", {}, mock_db, mock_usuario)

    data = _parse(result)
    assert len(data) == 1
    assert data[0]["numero_os"] == "OS202506-000001"


async def test_minhas_os_vazia(mock_db, mock_usuario):
    with patch("oficinas.agente.tools.OrdensServicoService") as MockOS:
        MockOS.return_value.listar = AsyncMock(return_value=[])
        result = await executar_tool("minhas_os", {}, mock_db, mock_usuario)

    assert _parse(result) == []


# ── tool desconhecida ─────────────────────────────────────────────────────────

async def test_tool_desconhecida_retorna_erro(mock_db, mock_usuario):
    result = await executar_tool("ferramenta_que_nao_existe", {}, mock_db, mock_usuario)

    assert "erro" in _parse(result)
