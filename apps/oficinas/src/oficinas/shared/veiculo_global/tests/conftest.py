import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.shared.veiculo_global.models import HistoricoVeiculo, Veiculo


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def veiculo() -> Veiculo:
    return Veiculo(
        id=uuid.uuid4(),
        placa="ABC1234",
        marca="Fiat",
        modelo="Uno",
        ano_fab=2015,
        ano_mod=2016,
        cor="Branco",
        tipo="carro",
        chassi=None,
        criado_em=datetime.now(timezone.utc),
    )


@pytest.fixture
def historico_publico(veiculo, tenant_id) -> HistoricoVeiculo:
    return HistoricoVeiculo(
        id=uuid.uuid4(),
        veiculo_id=veiculo.id,
        tenant_id=tenant_id,
        os_id=None,
        data_servico=date.today(),
        km_entrada=50000,
        resumo_publico="Troca de óleo e filtros",
        detalhe_privado="Óleo 5W30 sintético, filtro Mann",
        criado_em=datetime.now(timezone.utc),
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
    r.scalar_one.return_value = obj
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
