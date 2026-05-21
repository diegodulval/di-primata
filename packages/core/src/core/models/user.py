from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.models.enums import RolePerfil, TipoAgente


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    nome: str
    email: str
    tipo: TipoAgente
    senha_hash: str
    ativo: bool = True
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    nome: str
    email: str
    tipo: TipoAgente
    senha: str


class Profile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    user_id: UUID
    role: RolePerfil
    ativo: bool = True
