import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.modules.iam.models import Usuario


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def usuario_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_usuario(tenant_id, usuario_id) -> MagicMock:
    u = MagicMock(spec=Usuario)
    u.id = usuario_id
    u.tenant_id = tenant_id
    u.nome = "João Mecânico"
    u.numero_whatsapp = "+5511999999999"
    u.ativo = True
    return u


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    vazio = MagicMock()
    vazio.scalar_one_or_none.return_value = None
    vazio.scalars.return_value.all.return_value = []
    db.execute.return_value = vazio
    return db
