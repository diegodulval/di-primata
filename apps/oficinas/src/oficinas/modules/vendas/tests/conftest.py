import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.modules.estoque.models import Produto
from oficinas.modules.vendas.models import ItemVenda, Venda


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def produto(tenant_id) -> Produto:
    return Produto(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo="P001",
        descricao="Filtro de óleo",
        ncm=None,
        marca=None,
        localizacao=None,
        preco_custo=Decimal("20.00"),
        preco_venda=Decimal("30.00"),
        estoque_atual=Decimal("5.000"),
        estoque_minimo=Decimal("0"),
        estoque_maximo=Decimal("0"),
        ativo=True,
    )


@pytest.fixture
def venda(tenant_id) -> Venda:
    return Venda(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=uuid.uuid4(),
        cliente_id=None,
        numero_venda="VDA202506-ABC123",
        origem="BALCAO",
        total=Decimal("100.00"),
        status="CONCLUIDA",
        criado_em=datetime.now(timezone.utc),
    )


@pytest.fixture
def item_venda(venda, produto) -> ItemVenda:
    return ItemVenda(
        id=uuid.uuid4(),
        venda_id=venda.id,
        produto_id=produto.id,
        quantidade=Decimal("2.000"),
        preco_unitario=Decimal("50.00"),
        subtotal=Decimal("100.00"),
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
