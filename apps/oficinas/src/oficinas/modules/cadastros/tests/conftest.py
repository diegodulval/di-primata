import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.modules.cadastros.models import Cliente, ClienteVeiculo


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def cliente(tenant_id) -> Cliente:
    return Cliente(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        nome="João Silva",
        cpf_cnpj="12345678901",
        telefone="11999990000",
        email="joao@example.com",
        endereco="Rua das Flores, 10",
        criado_em=datetime.now(timezone.utc),
    )


@pytest.fixture
def veiculo_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def link_ativo(tenant_id, cliente, veiculo_id) -> ClienteVeiculo:
    return ClienteVeiculo(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        cliente_id=cliente.id,
        veiculo_id=veiculo_id,
        data_inicio=date(2024, 1, 1),
        data_fim=None,
        ativo=True,
    )


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    vazio = MagicMock()
    vazio.scalar_one_or_none.return_value = None
    vazio.scalars.return_value.all.return_value = []
    db.execute.return_value = vazio
    return db


def resultado_com(obj):
    r = MagicMock()
    r.scalar_one_or_none.return_value = obj
    return r


def resultado_lista(items: list):
    r = MagicMock()
    r.scalars.return_value.all.return_value = items
    return r


def resultado_vazio():
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    r.scalars.return_value.all.return_value = []
    return r
