from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import StatusCiclo


class Cycle(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    unit_id: UUID
    protocol_id: UUID
    codigo: str
    produto: str
    status: StatusCiclo = StatusCiclo.ABERTO
    iniciado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    encerrado_em: datetime | None = None
    insumos_json: list[dict[str, Any]] = Field(default_factory=list)
    meta_json: dict[str, Any] = Field(default_factory=dict)


class CycleCreate(BaseModel):
    unit_id: UUID
    protocol_id: UUID
    produto: str
    insumos_json: list[dict[str, Any]] = Field(default_factory=list)
    meta_json: dict[str, Any] = Field(default_factory=dict)
