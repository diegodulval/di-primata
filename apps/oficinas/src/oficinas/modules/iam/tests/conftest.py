import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.core.enums import Perfil
from oficinas.core.security import hash_senha
from oficinas.modules.iam.models import Usuario


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


def _usuario(tenant_id: uuid.UUID, perfil: Perfil, **kwargs) -> Usuario:
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        nome="Usuário Teste",
        email=None,
        senha_hash=hash_senha("dev1234"),
        perfil=perfil,
        numero_whatsapp=None,
        ativo=True,
        criado_em=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Usuario(**defaults)


@pytest.fixture
def usuario_admin(tenant_id):
    return _usuario(tenant_id, Perfil.ADMIN, nome="Admin Teste", email="admin@oficina.dev")


@pytest.fixture
def usuario_atendente(tenant_id):
    return _usuario(tenant_id, Perfil.ATENDENTE, nome="Atendente Teste", email="atendente@oficina.dev")


@pytest.fixture
def usuario_mecanico(tenant_id):
    return _usuario(tenant_id, Perfil.MECANICO, nome="Mecânico Teste", numero_whatsapp="+5511999990000")


@pytest.fixture
def mock_db():
    db = AsyncMock()
    # session.add() is synchronous in AsyncSession — override to avoid coroutine warnings
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


def resultado_vazio():
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    return r
