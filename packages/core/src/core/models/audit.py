from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    entidade_id: UUID
    entidade_tipo: str
    ator_id: UUID
    acao: str
    dados_antes: dict[str, Any] | None = None
    dados_depois: dict[str, Any] | None = None
    ip_origem: str | None = None
    ocorrido_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
