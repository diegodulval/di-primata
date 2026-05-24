from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oficinas.agente.worker import processar


def _make_end_turn(text: str) -> MagicMock:
    blk = MagicMock()
    blk.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [blk]
    return response


def _make_tool_use(tool_name: str, tool_id: str, tool_input: dict) -> MagicMock:
    blk = MagicMock()
    blk.type = "tool_use"
    blk.name = tool_name
    blk.id = tool_id
    blk.input = tool_input
    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [blk]
    return response


@patch("oficinas.agente.worker.sessao_mod")
@patch("oficinas.agente.worker.executar_tool")
@patch("oficinas.agente.worker.AsyncAnthropic")
async def test_processar_usuario_nao_encontrado(mock_anthropic, mock_exec_tool, mock_sessao, mock_db):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    result = await processar(mock_db, "+5511000000000", "oi")

    assert result is None
    mock_anthropic.assert_not_called()
    mock_sessao.salvar.assert_not_called()


@patch("oficinas.agente.worker.sessao_mod")
@patch("oficinas.agente.worker.executar_tool")
@patch("oficinas.agente.worker.AsyncAnthropic")
async def test_processar_end_turn_retorna_texto(
    mock_anthropic, mock_exec_tool, mock_sessao, mock_db, mock_usuario
):
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_usuario
    mock_db.get.return_value = MagicMock(razao_social="Oficina Teste")
    mock_sessao.carregar = AsyncMock(return_value=[])
    mock_sessao.salvar = AsyncMock()

    mock_client = AsyncMock()
    mock_client.messages.create.return_value = _make_end_turn("OS aberta com sucesso!")
    mock_anthropic.return_value = mock_client

    result = await processar(mock_db, "+5511999999999", "abra uma OS")

    assert result == "OS aberta com sucesso!"
    mock_client.messages.create.assert_called_once()
    mock_sessao.salvar.assert_called_once()


@patch("oficinas.agente.worker.sessao_mod")
@patch("oficinas.agente.worker.executar_tool")
@patch("oficinas.agente.worker.AsyncAnthropic")
async def test_processar_tool_use_depois_end_turn(
    mock_anthropic, mock_exec_tool, mock_sessao, mock_db, mock_usuario
):
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_usuario
    mock_db.get.return_value = MagicMock(razao_social="Oficina Teste")
    mock_sessao.carregar = AsyncMock(return_value=[])
    mock_sessao.salvar = AsyncMock()

    mock_client = AsyncMock()
    mock_client.messages.create.side_effect = [
        _make_tool_use("minhas_os", "tool_id_1", {}),
        _make_end_turn("Você tem 1 OS aberta."),
    ]
    mock_anthropic.return_value = mock_client
    mock_exec_tool.return_value = '{"lista": []}'

    result = await processar(mock_db, "+5511999999999", "minhas os")

    assert result == "Você tem 1 OS aberta."
    assert mock_client.messages.create.call_count == 2
    mock_exec_tool.assert_called_once_with("minhas_os", {}, mock_db, mock_usuario)
    mock_sessao.salvar.assert_called_once()


@patch("oficinas.agente.worker.sessao_mod")
@patch("oficinas.agente.worker.executar_tool")
@patch("oficinas.agente.worker.AsyncAnthropic")
async def test_processar_inclui_historico_existente(
    mock_anthropic, mock_exec_tool, mock_sessao, mock_db, mock_usuario
):
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_usuario
    mock_db.get.return_value = MagicMock(razao_social="Oficina Teste")

    historico = [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "Olá!"},
    ]
    mock_sessao.carregar = AsyncMock(return_value=historico)
    mock_sessao.salvar = AsyncMock()

    mock_client = AsyncMock()
    mock_client.messages.create.return_value = _make_end_turn("Como posso ajudar?")
    mock_anthropic.return_value = mock_client

    await processar(mock_db, "+5511999999999", "nova mensagem")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    msgs_enviadas = call_kwargs["messages"]
    # call_args guarda referência ao mesmo objeto — após a chamada o worker
    # adiciona a resposta do assistente, então o índice fixo é mais confiável
    assert msgs_enviadas[0] == historico[0]
    assert msgs_enviadas[1] == historico[1]
    assert msgs_enviadas[2] == {"role": "user", "content": "nova mensagem"}
