import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.core.enums import StatusOS, TipoItem
from oficinas.modules.estoque.models import Produto
from oficinas.modules.ordens_servico.models import ItemOS, OrdemServico


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mecanico_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def cliente_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def veiculo_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def os_aberta(tenant_id, mecanico_id, cliente_id, veiculo_id) -> OrdemServico:
    return OrdemServico(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mecanico_id=mecanico_id,
        cliente_id=cliente_id,
        veiculo_id=veiculo_id,
        numero_os="OS202506-ABC123",
        km_entrada=50000,
        descricao_problema="Troca de óleo e filtro",
        status=StatusOS.ABERTA,
        compartilhar_historico=False,
        aberta_em=datetime.now(timezone.utc),
        fechada_em=None,
        total_pecas=Decimal("0"),
        total_servicos=Decimal("0"),
        desconto=Decimal("0"),
        total_final=Decimal("0"),
    )


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
def item_peca(os_aberta, produto) -> ItemOS:
    return ItemOS(
        id=uuid.uuid4(),
        os_id=os_aberta.id,
        produto_id=produto.id,
        tipo=TipoItem.PECA,
        descricao="Filtro de óleo",
        quantidade=Decimal("2.000"),
        preco_unitario=Decimal("30.00"),
        subtotal=Decimal("60.00"),
    )


@pytest.fixture
def item_servico(os_aberta) -> ItemOS:
    return ItemOS(
        id=uuid.uuid4(),
        os_id=os_aberta.id,
        produto_id=None,
        tipo=TipoItem.SERVICO,
        descricao="Mão de obra",
        quantidade=Decimal("1.000"),
        preco_unitario=Decimal("100.00"),
        subtotal=Decimal("100.00"),
    )


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.delete = MagicMock()
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
