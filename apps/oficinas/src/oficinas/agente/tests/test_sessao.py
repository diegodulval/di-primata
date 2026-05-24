import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.agente.sessao import TIMEOUT, carregar, salvar


def _row(msgs, delta: timedelta = timedelta(minutes=1)) -> MagicMock:
    r = MagicMock()
    r.mensagens = msgs
    r.atualizado_em = datetime.now(timezone.utc) - delta
    return r


async def test_carregar_sem_sessao(mock_db):
    mock_db.execute.return_value.fetchone.return_value = None

    result = await carregar(mock_db, "+5511999999999")

    assert result == []


async def test_carregar_sessao_ativa(mock_db):
    msgs = [{"role": "user", "content": "oi"}]
    mock_db.execute.return_value.fetchone.return_value = _row(msgs)

    result = await carregar(mock_db, "+5511999999999")

    assert result == msgs


async def test_carregar_sessao_expirada(mock_db):
    msgs = [{"role": "user", "content": "oi"}]
    expirado = TIMEOUT + timedelta(seconds=1)
    mock_db.execute.return_value.fetchone.return_value = _row(msgs, delta=expirado)

    result = await carregar(mock_db, "+5511999999999")

    assert result == []


async def test_carregar_mensagens_como_string_json(mock_db):
    msgs = [{"role": "user", "content": "oi"}]
    r = MagicMock()
    r.mensagens = json.dumps(msgs)
    r.atualizado_em = datetime.now(timezone.utc)
    mock_db.execute.return_value.fetchone.return_value = r

    result = await carregar(mock_db, "+5511999999999")

    assert result == msgs


async def test_salvar_executa_upsert_e_commit(mock_db):
    numero = "+5511999999999"
    tid = str(uuid.uuid4())
    uid = str(uuid.uuid4())
    msgs = [{"role": "user", "content": "oi"}]

    await salvar(mock_db, numero=numero, tenant_id=tid, usuario_id=uid, msgs=msgs)

    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
    call_args = mock_db.execute.call_args
    bound_params = call_args[0][1]
    assert bound_params["n"] == numero
    assert bound_params["tid"] == tid
    assert bound_params["uid"] == uid
    assert json.loads(bound_params["msgs"]) == msgs
    # garante que não usa ::uuid/::jsonb (quebra com SQLAlchemy+asyncpg)
    sql_text = str(mock_db.execute.call_args[0][0])
    assert "::" not in sql_text
