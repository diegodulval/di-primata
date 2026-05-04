from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import EstadoAgente, TipoEvento


class EventoCaptura(BaseModel):
    device_id: str
    capturado_em: datetime
    tipo_evento: TipoEvento
    payload: dict[str, Any] = Field(default_factory=dict)


class PrimataSessao(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    agente_id: UUID
    ciclo_id: UUID | None = None
    device_id: str
    estado: EstadoAgente = EstadoAgente.OCIOSO
    contexto_json: dict[str, Any] = Field(default_factory=dict)
    offline_queue: list[EventoCaptura] = Field(default_factory=list)
    kb_setor: str
    kb_hash: str
    modelo_ia_ver: str
    iniciada_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ultimo_sync: datetime | None = None
