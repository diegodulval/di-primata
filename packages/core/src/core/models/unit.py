from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.models.enums import TipoUnidade


class Unit(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    nome: str
    tipo: TipoUnidade
    area_capacidade: float | None = None
    lat: float | None = None
    lng: float | None = None
    setor_template: str
    ativo: bool = True
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnitCreate(BaseModel):
    nome: str
    tipo: TipoUnidade
    area_capacidade: float | None = None
    lat: float | None = None
    lng: float | None = None
    setor_template: str
